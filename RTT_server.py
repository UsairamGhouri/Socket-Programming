import socket
from datetime import datetime
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('localhost', 12345))
print("UDP Server running on localhost:12345")
while True:
    data, client_address = server_socket.recvfrom(1024)
    message = data.decode()
    if message.lower() == "exit":
        break
    response = f"{message} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    server_socket.sendto(response.encode(), client_address)
server_socket.close()
