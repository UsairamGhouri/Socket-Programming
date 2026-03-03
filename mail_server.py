import socket
import threading

clients = {} 

def handle_client(conn, addr):
    username = conn.recv(1024).decode()
    clients[username] = (conn, addr)
    print(f"{username} connected from {addr}")

    while True:
        data = conn.recv(1024).decode()
        if not data or data.lower() == "exit":
            break
        if ':' in data:
            recipient, message = data.split(':', 1)
            if recipient in clients:
                recipient_conn, _ = clients[recipient]
                recipient_conn.sendall(f"Mail from {username}: {message}".encode())
            else:
                conn.sendall(f"User {recipient} not found.".encode())
        else:
            conn.sendall("Invalid format. Use recipient:message".encode())
    print(f"{username} disconnected")
    del clients[username]
    conn.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 12345))
    server.listen(5)
    print("Mail server started on port 12345.")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()