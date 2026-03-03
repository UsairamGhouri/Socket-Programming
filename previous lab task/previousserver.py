import socket
import threading
import os

# Server settings
IP = "127.0.0.1"  # Localhost
PORT = 8080
BUFFER_SIZE = 1024

# Dictionary to keep track of connected clients: {name: socket_object}
clients = {}

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    
    try:
        # First thing client does is send their name
        name = conn.recv(BUFFER_SIZE).decode()
        clients[name] = conn
        print(f"[REGISTERED] {name} is now online.")

        while True:
            # Wait for instructions from client
            message = conn.recv(BUFFER_SIZE).decode()
            if not message:
                break
            
            if message.startswith("SEND_FILE"):
                # Format: SEND_FILE|recipient_name|filename
                _, recipient, filename = message.split("|")
                
                # Receive the actual file data
                file_data = conn.recv(4096)
                
                if recipient in clients:
                    # Forward the file to the chosen recipient
                    target_conn = clients[recipient]
                    target_conn.send(f"INCOMING|{filename}".encode())
                    target_conn.send(file_data)
                    conn.send(f"Success: File sent to {recipient}".encode())
                else:
                    conn.send("Error: Recipient not found.".encode())

    except:
        print(f"[ERROR] Connection lost with {addr}")
    finally:
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((IP, PORT))
    server.listen()
    print(f"[LISTENING] Server is running on {IP}:{PORT}")

    while True:
        conn, addr = server.accept()
        # Start a new thread for each client
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    # Create a folder for server files if it doesn't exist
    if not os.path.exists("server_storage"):
        os.makedirs("server_storage")
    start_server()