
import socket
import datetime
# 1. Create UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# 2. Bind server to localhost and port 12346
server_socket.bind(('localhost', 12346))
print("UDP Server is running and waiting for client request...")
# 3. Receive message from client
data, addr = server_socket.recvfrom(1024)
print("Received message from client:", data.decode())
# 4. Get current date and time
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# 5. Send date and time back to client
server_socket.sendto(current_time.encode(), addr)
    
