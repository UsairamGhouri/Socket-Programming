import socket
import threading
import os

def receive_handler(s):
    """Background listener for incoming files from other clients."""
    while True:
        try:
            data = s.recv(1024).decode()
            if data.startswith("INCOMING"):
                _, sender, filename, filesize = data.split("|")
                filesize = int(filesize)
                
                print(f"\n[!] Receiving file '{filename}' from {sender}...")
                
                # Save the file with a prefix to show it was received
                with open("received_" + filename, "wb") as f:
                    remaining = filesize
                    while remaining > 0:
                        chunk = s.recv(min(remaining, 4096))
                        f.write(chunk)
                        remaining -= len(chunk)
                
                print(f"[OK] File saved as 'received_{filename}'")
                print("1. Send File  2. Exit: ", end="")
        except:
            break

# Connection
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 12345))

# Register
reg_msg = s.recv(1024).decode()
my_email = input(reg_msg)
s.send(my_email.encode())

# Start background listener
threading.Thread(target=receive_handler, args=(s,), daemon=True).start()

while True:
    print("\n--- File Sharing Menu ---")
    print("1. Send File to a Client")
    print("2. Exit")
    choice = input("Choice: ")

    if choice == '1':
        target = input("Recipient Email: ")
        file_path = input("Enter path of file to send: ")

        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            filesize = os.path.getsize(file_path)
            
            # Send the "Header" so server knows what to do
            header = f"FILE|{target}|{filename}|{filesize}"
            s.send(header.encode())
            
            # Send the actual file data
            with open(file_path, "rb") as f:
                s.sendall(f.read())
            
            print("File data sent to server...")
        else:
            print("Error: File not found.")

    elif choice == '2':
        break

s.close()