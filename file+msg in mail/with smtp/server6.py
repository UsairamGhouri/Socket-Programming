import socket
import threading

# Configuration
HOST = '127.0.0.1'
PORT = 8080
clients = {} # Stores {email: socket_connection}

def handle_client(conn, addr):
    try:
        # Step 1: Registration
        conn.send("REG_EMAIL".encode())
        user_email = conn.recv(1024).decode()
        clients[user_email] = conn
        print(f"[CONNECTED] {user_email} from {addr}")

        while True:
            # Step 2: Receive Command
            # Format: FILE|recipient|filename|filesize
            header = conn.recv(1024).decode()
            if not header: break

            if header.startswith("FILE"):
                parts = header.split("|")
                target = parts[1]
                fname = parts[2]
                fsize = int(parts[3])

                if target in clients:
                    target_conn = clients[target]
                    # Notify target
                    target_conn.send(f"INCOMING|{user_email}|{fname}|{fsize}".encode())
                    
                    # Relay the file data
                    remaining = fsize
                    while remaining > 0:
                        chunk = conn.recv(min(remaining, 4096))
                        target_conn.send(chunk)
                        remaining -= len(chunk)
                    
                    conn.send("SUCCESS: File relayed.".encode())
                else:
                    conn.send("ERROR: Recipient not online.".encode())

    except:
        pass
    finally:
        conn.close()
        # Clean up on disconnect
        for e, c in list(clients.items()):
            if c == conn:
                del clients[e]
                print(f"[DISCONNECTED] {e}")

# Start Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
print(f"Server is running on {HOST}:{PORT}")

while True:
    conn, addr = server.accept()
    threading.Thread(target=handle_client, args=(conn, addr)).start()