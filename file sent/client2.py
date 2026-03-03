import socket
import threading
import os

def receive_handler(client_socket):
    """Listens for files being sent to us from the server."""
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if data.startswith("INCOMING"):
                # Split the info
                _, sender, filename, filesize = data.split("|")
                filesize = int(filesize)
                
                print(f"\nReceiving '{filename}' from {sender}...")
                
                # Save the file
                with open("received_" + filename, "wb") as f:
                    remaining = filesize
                    while remaining > 0:
                        chunk = client_socket.recv(min(remaining, 4096))
                        f.write(chunk)
                        remaining -= len(chunk)
                
                print(f"File saved as 'received_{filename}'")
                print("Enter target name to send to (or 'exit'): ", end="")
        except:
            break

# Connect to server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 9999))

name = input("Enter your name: ")
client.send(name.encode())

# Start the background listener for incoming files
threading.Thread(target=receive_handler, args=(client,), daemon=True).start()

while True:
    target = input("Enter target name to send to (or 'exit'): ")
    if target.lower() == 'exit':
        break
        
    file_path = input("Enter the filename to send: ")
    
    if os.path.exists(file_path):
        filesize = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        # Send info header
        header = f"{target}|{filename}|{filesize}"
        client.send(header.encode())
        
        # Send the actual file
        with open(file_path, "rb") as f:
            client.sendall(f.read())
        print("File sent!")
    else:
        print("File does not exist locally.")

client.close()