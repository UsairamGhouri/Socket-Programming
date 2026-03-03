import socket

# 1. Create UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# 2. Server address and port
server_address = ('localhost', 12345)
# 3. Send request for datetime
client_socket.sendto(b"Requesting current date and time", server_address) 
# 4. Receive the datetime from the server
data, addr = client_socket.recvfrom(1024)
print("Current Date and Time from Server:", data.decode())
# 5. Close socket
client_socket.close()