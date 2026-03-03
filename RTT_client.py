import socket
import time
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 12345)
while True:
    message = input("Enter message ('exit' to quit): ")
    if message.lower() == "exit":
        client_socket.sendto(message.encode(), server_address)
        break
    start_time = time.time()
    client_socket.sendto(message.encode(), server_address)
    response, _ = client_socket.recvfrom(1024)
    rtt = (time.time() - start_time) * 1000
    print(f"Server response: {response.decode()}")
    print(f"RTT: {rtt:.2f} ms")
client_socket.close()
