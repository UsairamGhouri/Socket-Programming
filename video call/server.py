import socket
import threading
import struct

HOST = '127.0.0.1'
PORT = 7777
clients = {} # {email: socket}

def handle_video(conn, addr):
    try:
        # Step 1: Register client email
        conn.send("REG".encode())
        email = conn.recv(1024).decode()
        clients[email] = conn
        print(f"[VIDEO SERVER] {email} connected.")

        while True:
            # Step 2: Receive target email (20 bytes) and frame size (8 bytes)
            header = conn.recv(28)
            if not header: break

            target_email = header[:20].decode().strip()
            msg_size = struct.unpack(">Q", header[20:])[0] # Get the size of the incoming image

            # Step 3: Receive the actual image data
            data = b""
            while len(data) < msg_size:
                data += conn.recv(4096)
            
            # Step 4: Relay to target
            if target_email in clients:
                # Send the size first, then the data
                target_conn = clients[target_email]
                target_conn.sendall(struct.pack(">Q", msg_size) + data)
    except:
        pass

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
print("Video Relay Server is active...")

while True:
    c, a = server.accept()
    threading.Thread(target=handle_video, args=(c, a)).start()