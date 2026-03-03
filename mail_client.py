import socket
import threading

def receive_messages(sock):
    while True:
        try:
            data = sock.recv(1024).decode()
            if not data:
                break
            print("\n" + data)
        except:
            break

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 12345))
    username = input("Enter your username: ")
    client.sendall(username.encode())

    threading.Thread(target=receive_messages, args=(client,), daemon=True).start()

    while True:
        msg = input("Enter message (format recipient:message, or 'exit' to quit): ")
        if msg.lower() == "exit":
            client.sendall(msg.encode())
            break
        client.sendall(msg.encode())
    client.close()

if __name__ == "__main__":
    main()