import socket
import time
import threading
import os

def receive_handler(client_socket):
    """Handles incoming messages and file transfers from the server."""
    while True:
        try:
            data, _ = client_socket.recvfrom(65535)
            if data.startswith(b"FILE_FROM:"):
                first_colon = data.find(b":")
                second_colon = data.find(b":", first_colon + 1)
                third_colon = data.find(b":", second_colon + 1)
                
                header = data[:third_colon].decode()
                file_content = data[third_colon + 1:]
                
                _, sender, filename = header.split(":")
                save_path = f"received_{filename}"
                
                with open(save_path, "wb") as f:
                    f.write(file_content)
                print(f"\n[File received from {sender}: {filename} saved as {save_path}]")
            else:
                print(f"\n{data.decode()}")
        except Exception as e:
            print(f"\nConnection closed or error: {e}")
            break

def main():
    server_addr = ('localhost', 12345)
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    start_time = time.time()
    client.sendto(b"PING", server_addr)
    
    try:
        client.settimeout(2.0)
        data, _ = client.recvfrom(1024)
        rtt = (time.time() - start_time) * 1000
        if data.decode() == "PONG":
            print(f"Server active. Round Trip Time (RTT): {rtt:.2f} ms")
    except socket.timeout:
        print("Server connection failed (Timeout).")
        return
    finally:
        client.settimeout(None)

    username = input("Enter your username: ")
    client.sendto(f"REGISTER:{username}".encode(), server_addr)

    threading.Thread(target=receive_handler, args=(client,), daemon=True).start()

    print("\nCommands:")
    print(" - '<recipient>:message' to send a text message")
    print(" - 'FILE:<recipient>:filepath' to send a file")
    print(" - 'exit' to quit")

    while True:
        try:
            cmd = input("> ")
            if cmd.lower() == "exit":
                break
            
            if cmd.startswith("FILE:"):
                try:
                    _, recipient, filepath = cmd.split(":", 2)
                    if os.path.exists(filepath):
                        filename = os.path.basename(filepath)
                        with open(filepath, "rb") as f:
                            file_data = f.read()
                        
                        header = f"SEND_FILE:{recipient}:{filename}:".encode()
                        client.sendto(header + file_data, server_addr)
                        print(f"File '{filename}' sent to {recipient}")
                    else:
                        print("Error: File not found.")
                except ValueError:
                    print("Usage: FILE:recipient:filepath")
            elif ":" in cmd:
                client.sendto(cmd.encode(), server_addr)
            else:
                print("Invalid format. Use '<recipient>:<message>' or 'FILE:<recipient>:<filepath>'")
        except EOFError:
            break

    client.close()

if __name__ == "__main__":
    main()