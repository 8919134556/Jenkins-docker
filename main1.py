import socket
import concurrent.futures
import configparser
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
import queue
import threading
import multiprocessing

Base = declarative_base()

class CommsRawData(Base):
    __tablename__ = 'comms_raw_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date_time = Column(String)
    raw_data = Column(String)

class CommsGpsData(Base):
    __tablename__ = 'comms_gps_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_name = Column(String)
    latitude = Column(String)
    longitude = Column(String)

class HexStringConverter:
    @staticmethod
    def hex_to_string(hex_string):
        try:
            return bytes.fromhex(hex_string).decode('utf-8')
        except UnicodeDecodeError as e:
            print(f"Error converting hex to string: {e}")

    @staticmethod
    def string_to_hex(input_string):
        try:
            return input_string.encode('utf-8').hex()
        except Exception as e:
            print(f"Error converting string to hex: {e}")

class Config:
    def __init__(self, env):
        self.cf = configparser.ConfigParser()
        self.cf.read("settings1.config")
        if env not in self.cf.sections():
            raise ValueError(f"'{env}' environment not found in the settings.config file.")
        self.ip_address = self.cf.get(env, 'ip_address')
        self.port_number = int(self.cf.get(env, 'port_number'))
        self.database_url = self.cf.get(env, 'database_url')
        self.log_folder_path = self.cf.get(env, 'log_folder_path')

class DatabaseManager:
    def __init__(self, config):
        self.engine = create_engine(config.database_url, echo=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_data(self, data_model, **data_fields):
        session = self.Session()
        try:
            new_data = data_model(**data_fields)
            session.add(new_data)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error inserting data into {data_model.__tablename__}: {e}")

class LogCreation:
    def __init__(self, config, log_queue):
        self.config = config
        self.LOGS_FOLDER = self.config.log_folder_path
        self.log_queue = log_queue

    def log_data(self, log_type, data):
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            log_folder_path = os.path.join(self.LOGS_FOLDER, current_date)

            if not os.path.exists(log_folder_path):
                os.makedirs(log_folder_path)

            log_file_name = f"{log_type}_data.log"
            log_file_path = os.path.join(log_folder_path, log_file_name)

            log_entry = f'currenttime: {current_time} - {data}\n'
            self.log_queue.put((log_file_path, log_entry))
            print(f"Logged {log_type} data")
        except Exception as e:
            print(f"Error logging {log_type} data: {e}")

class LogWriter:
    def __init__(self, log_queue):
        self.log_queue = log_queue
        self.stop_event = threading.Event()

    def write_logs(self):
        while not self.stop_event.is_set():
            try:
                log_file_path, log_entry = self.log_queue.get(timeout=1)
                with open(log_file_path, "a") as log_file:
                    log_file.write(log_entry)
            except queue.Empty:
                pass

    def stop(self):
        self.stop_event.set()

class SocketServer:
    def __init__(self, config):
        self.HOST = config.ip_address
        self.PORT = config.port_number
        self.db_manager = DatabaseManager(config)
        self.converter = HexStringConverter()
        self.log_queue = queue.Queue()
        self.log_creation = LogCreation(config, self.log_queue)
        self.log_writer = LogWriter(self.log_queue)

    def handle_client(self, client_socket):
        with client_socket:
            hex_data = client_socket.recv(1024).decode('utf-8')
            logdatetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db_manager.add_data(CommsRawData, date_time=logdatetime, raw_data=hex_data)
            decoded_data = self.converter.hex_to_string(hex_data)
            if decoded_data:
                clientname, latitude, longitude = map(str.strip, decoded_data.split(','))
                self.db_manager.add_data(CommsGpsData, client_name=clientname, latitude=latitude, longitude=longitude)
                self.log_creation.log_data("client", f'client_name: {clientname}, latitude: {latitude}, longitude: {longitude}')
                self.log_creation.log_data("raw", hex_data)
            else:
                self.log_creation.log_data("error", decoded_data)

    def start(self):
        self.log_writer_thread = threading.Thread(target=self.log_writer.write_logs)
        self.log_writer_thread.start()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.HOST, self.PORT))
            server_socket.listen(1000)  # Maximum queued connections
            print(f"Server started on {self.HOST}:{self.PORT}")
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                while True:
                    client_socket, _ = server_socket.accept()
                    executor.submit(self.handle_client, client_socket)

    def stop(self):
        self.log_writer.stop()
        self.log_writer_thread.join()

def start_server(env):
    config = Config(env)
    server = SocketServer(config)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

if __name__ == "__main__":
    # Create multiple processes to handle the server
    num_processes = 2  # Adjust the number of server processes as needed
    processes = []

    for _ in range(num_processes):
        process = multiprocessing.Process(target=start_server, args=("dev",))
        process.daemon = True
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

