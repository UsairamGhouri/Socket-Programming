# DateTime TCP Server
import socket
import datetime

# 1. Create TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 2. Bind server to IP & port
server_socket.bind(('localhost', 12345))

# 3. Start listening
server_socket.listen(1)
print("DateTime Server is running on port 12345...")

while True:
    # 4. Accept connection
    connection, address = server_socket.accept()
    print("Connected to:", address)

    # 5. Get current date & time
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 6. Send datetime to client
    connection.send(now.encode())

    # 7. Close connection
    connection.close()
