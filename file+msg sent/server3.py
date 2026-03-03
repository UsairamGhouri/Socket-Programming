import socket
import threading

# Configuration
HOST = '127.0.0.1'
PORT = 6666
clients = {} # Store {name: socket}

def handle_client(conn, addr):
    try:
        # First message from client is always their name
        name = conn.recv(1024).decode()
        clients[name] = conn
        print(f"[JOINED] {name} is online.")

        while True:
            # Receive the command header
            header = conn.recv(1024).decode()
            if not header:
                break

            # Process commands: MSG|target|content OR FILE|target|filename|size
            parts = header.split("|")
            command = parts[0]
            target = parts[1]

            if target in clients:
                target_conn = clients[target]
                
                if command == "MSG":
                    content = parts[2]
                    # Forward message to target: FROM|name|message
                    target_conn.send(f"FROM_MSG|{name}|{content}".encode())
                
                elif command == "FILE":
                    filename = parts[2]
                    filesize = int(parts[3])
                    # Notify target: FROM_FILE|name|filename|size
                    target_conn.send(f"FROM_FILE|{name}|{filename}|{filesize}".encode())
                    
                    # Receive file from sender and send directly to target
                    remaining = filesize
                    while remaining > 0:
                        chunk = conn.recv(min(remaining, 4096))
                        target_conn.send(chunk)
                        remaining -= len(chunk)
            else:
                conn.send("SYSTEM|Error: User not found.".encode())

    except:
        pass
    finally:
        conn.close()
        # Remove client from dictionary on disconnect
        for n, c in list(clients.items()):
            if c == conn:
                print(f"[LEFT] {n} went offline.")
                del clients[n]

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
print(f"Server started on {HOST}:{PORT}")

while True:
    conn, addr = server.accept()
    threading.Thread(target=handle_client, args=(conn, addr)).start()