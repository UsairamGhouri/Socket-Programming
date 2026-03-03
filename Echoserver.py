import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

HOST = 'localhost'
PORT = 12345
server_socket.bind((HOST, PORT))

server_socket.listen(1)
print(f"Echo Server listening on {HOST}:{PORT}")

client_socket, client_address = server_socket.accept()
print(f"Connected to {client_address}")

while True:
    data = client_socket.recv(1024)
    if not data:
        break
    
    message = data.decode('utf-8')
    print(f"Received: {message}")
    
    client_socket.send(data)

client_socket.close()
server_socket.close()
print("Server closed")
