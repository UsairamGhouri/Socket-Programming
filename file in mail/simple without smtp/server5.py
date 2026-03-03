import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

# Stores {email: socket_connection}
clients = {}

def handle_client(conn, addr):
    try:
        # Step 1: Registration
        conn.send("WELCOME: Please enter your email: ".encode())
        user_email = conn.recv(1024).decode()
        clients[user_email] = conn
        print(f"[ONLINE] {user_email} has connected.")

        while True:
            # Step 2: Wait for command (FILE|recipient|filename|filesize)
            header = conn.recv(1024).decode()
            if not header: break

            if header.startswith("FILE"):
                _, recipient, filename, filesize = header.split("|")
                filesize = int(filesize)

                if recipient in clients:
                    target_conn = clients[recipient]
                    
                    # Notify the recipient a file is coming
                    target_conn.send(f"INCOMING|{user_email}|{filename}|{filesize}".encode())
                    
                    # Receive file from sender and immediately send to receiver
                    print(f"[RELAY] Forwarding {filename} to {recipient}...")
                    remaining = filesize
                    while remaining > 0:
                        chunk = conn.recv(min(remaining, 4096))
                        target_conn.send(chunk)
                        remaining -= len(chunk)
                    
                    conn.send("TRANSFER_COMPLETE".encode())
                else:
                    conn.send("ERROR: Recipient is not online.".encode())

    except:
        pass
    finally:
        conn.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
print("Server is listening for file transfers...")

while True:
    c, a = server.accept()
    threading.Thread(target=handle_client, args=(c, a)).start()