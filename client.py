import socket

def client_program():
    host = "localhost"  # or the IP address of the machine where the Docker container is running
    port = 5000

    client_socket = socket.socket()
    client_socket.connect((host, port))

    while True:
        message = input("Enter your message ('exit' to quit): ")
        if message == "exit":
            break
        client_socket.send(message.encode())
        response = client_socket.recv(1024).decode()
        print(f"Server: {response}")

    client_socket.close()

if __name__ == "__main__":
    client_program()
