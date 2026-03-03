import socket
import threading

# Server Setup
HOST = '127.0.0.1'
PORT = 5555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

# List to store all active client connections
all_clients = []

def broadcast(message, sender_conn):
    """Sends a message to everyone except the person who sent it."""
    for client in all_clients:
        if client != sender_conn:
            try:
                client.send(message)
            except:
                client.close()
                all_clients.remove(client)

def handle_client(conn):
    while True:
        try:
            # Receive message from client
            msg = conn.recv(1024)
            if not msg:
                break
            print(f"Relaying message: {msg.decode()}")
            broadcast(msg, conn)
        except:
            break
    
    conn.close()
    all_clients.remove(conn)

print("Server is running and waiting for clients...")

while True:
    conn, addr = server.accept()
    print(f"Connected with {str(addr)}")
    
    all_clients.append(conn)
    
    # Start a thread so the server can talk to this client separately
    thread = threading.Thread(target=handle_client, args=(conn,))
    thread.start()