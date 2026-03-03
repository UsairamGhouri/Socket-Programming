# DateTime TCP Client
import socket

# 1. Create TCP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 2. Connect to server
client_socket.connect(('localhost', 12345))

# 3. Receive date & time from server
data = client_socket.recv(1024).decode()
print("Current Date & Time from Server:", data)

# 4. Close socket
client_socket.close()

