import socket
import threading

# Server Config
HOST = '127.0.0.1'
PORT = 9999

# Dictionary to store { "Name": connection_object }
clients = {}

def handle_client(conn, addr):
    # Step 1: Get the name from the client upon joining
    try:
        my_name = conn.recv(1024).decode()
        clients[my_name] = conn
        print(f"{my_name} has joined from {addr}")

        while True:
            # Step 2: Listen for instructions
            # Format expected: "RECIPIENT_NAME|FILENAME|FILE_SIZE"
            instruction = conn.recv(1024).decode()
            if not instruction:
                break

            target_name, filename, filesize = instruction.split("|")
            filesize = int(filesize)

            if target_name in clients:
                target_conn = clients[target_name]
                
                # Tell the receiver a file is coming
                notification = f"INCOMING|{my_name}|{filename}|{filesize}"
                target_conn.send(notification.encode())

                # Step 3: Receive file data from sender and pass it to receiver
                remaining = filesize
                while remaining > 0:
                    chunk = conn.recv(min(remaining, 4096))
                    target_conn.send(chunk)
                    remaining -= len(chunk)
                
                print(f"Success: {my_name} sent {filename} to {target_name}")
            else:
                conn.send("ERROR: User not found".encode())

    except:
        pass
    finally:
        # Cleanup if client disconnects
        if 'my_name' in locals():
            print(f"{my_name} disconnected.")
            del clients[my_name]
        conn.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
print("Server is waiting for clients...")

while True:
    conn, addr = server.accept()
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()