import socket
import threading
import os

def background_listener(s):
    """Handles all data coming FROM the server."""
    while True:
        try:
            data = s.recv(1024).decode()
            parts = data.split("|")
            type = parts[0]

            if type == "FROM_MSG":
                sender, msg = parts[1], parts[2]
                print(f"\n[Message from {sender}]: {msg}")
            
            elif type == "FROM_FILE":
                sender, fname, fsize = parts[1], parts[2], int(parts[3])
                print(f"\n[File from {sender}]: Receiving {fname}...")
                with open("received_" + fname, "wb") as f:
                    remaining = fsize
                    while remaining > 0:
                        chunk = s.recv(min(remaining, 4096))
                        f.write(chunk)
                        remaining -= len(chunk)
                print(f"File saved as 'received_{fname}'")
            
            elif type == "SYSTEM":
                print(f"\n[Server]: {parts[1]}")
            
            print("\nSelect: 1.Send Msg 2.Send File 3.Exit: ", end="")
        except:
            break

# Connection setup
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 6666))

my_name = input("Enter your name: ")
client.send(my_name.encode())

# Start listening in background
threading.Thread(target=background_listener, args=(client,), daemon=True).start()

while True:
    choice = input("\nSelect: 1.Send Msg 2.Send File 3.Exit: ")
    
    if choice == '1':
        target = input("Target Name: ")
        msg = input("Message: ")
        client.send(f"MSG|{target}|{msg}".encode())
    
    elif choice == '2':
        target = input("Target Name: ")
        fpath = input("Filename/Path: ")
        if os.path.exists(fpath):
            fname = os.path.basename(fpath)
            fsize = os.path.getsize(fpath)
            client.send(f"FILE|{target}|{fname}|{fsize}".encode())
            with open(fpath, "rb") as f:
                client.sendall(f.read())
            print("File uploaded to server.")
        else:
            print("File not found!")
            
    elif choice == '3':
        break

client.close()