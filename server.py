import socket
import sqlite3

class SocketServer:

    def __init__(self, host="0.0.0.0", port=5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket()
        self.db_connection = self.create_database_connection()

    @staticmethod
    def create_database_connection():
        connection = sqlite3.connect('data.db')
        cursor = connection.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            client_name TEXT,
            latitude TEXT,
            longitude TEXT
        )
        """)
        connection.commit()
        return connection
    @staticmethod
    def decode_data(data):
        try:
            return bytes.fromhex(data).decode('utf-8')
        except Exception as e:
            print(f"Error decoding data: {e}")
            return None

    def handle_client(self, conn):
        while True:
            try:
                data = conn.recv(1024).decode()
                if not data:
                    print("Connection ended by the client.")
                    return
                
                decoded_str = self.decode_data(data)
                if not decoded_str:
                    return

                print(f"Received (Decoded): {decoded_str}")

                client_name, lat, lon = decoded_str.split(', ')
                latitude = lat.split('=')[1]
                longitude = lon.split('=')[1]

                cursor = self.db_connection.cursor()
                cursor.execute("INSERT INTO messages (client_name, latitude, longitude) VALUES (?, ?, ?)", 
                            ("1", latitude, longitude))
                self.db_connection.commit()
                conn.send("Data saved!".encode())

            except ConnectionAbortedError:
                print("Connection was aborted by the client.")
                return

            except Exception as e:
                print(f"An error occurred: {e}")
                return

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        print(f"Server listening on {self.port}")

        try:
            while True:
                print("Waiting for a client connection...")
                conn, address = self.server_socket.accept()
                print(f"Connection from {address}")
                self.handle_client(conn)
        except KeyboardInterrupt:
            print("\nShutting down server.")
            self.db_connection.close()
            self.server_socket.close()

if __name__ == "__main__":
    server = SocketServer()
    server.start()
