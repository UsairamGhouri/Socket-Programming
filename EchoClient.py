import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

HOST = 'localhost'
PORT = 12345
client_socket.connect((HOST, PORT))
print("Connected to server")

while True:
    message = input("Enter message: ")
    if message.lower() == 'exit':
        break
    
    client_socket.send(message.encode('utf-8'))
    
    response = client_socket.recv(1024)
    print(f"Echo: {response.decode('utf-8')}")

client_socket.close()
print("Disconnected")