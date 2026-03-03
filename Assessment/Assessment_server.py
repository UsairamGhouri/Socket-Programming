import socket
import threading

IP = "127.0.0.1"
PORT = 12345
BUFFER_SIZE = 65535  

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((IP, PORT))

clients = {}   
usernames = {} 

def handle_packet(data, address):
    try:
        try:
            message = data.decode('utf-8')
        except UnicodeDecodeError:
            message = None
            
        if message and message == "PING":
            server_socket.sendto("PONG".encode('utf-8'), address)
            return

        if message and message.startswith("REGISTER:"):
            username = message.split(":", 1)[1].strip()
            if not username:
                return
            clients[address] = username
            usernames[username] = address
            print(f"Registered user '{username}' at {address}")
            server_socket.sendto(f"Welcome {username}! You are now registered.".encode(), address)
            return

        if data.startswith(b"SEND_FILE:"):
            try:
                first = data.find(b":")
                second = data.find(b":", first + 1)
                third = data.find(b":", second + 1)
                
                if first != -1 and second != -1 and third != -1:
                    header_part = data[:third].decode()
                    _, recipient, filename = header_part.split(":")
                    
                    recipient = recipient.strip("<>")
                    
                    file_content = data[third+1:] 
                    
                    sender_name = clients.get(address, f"Unknown")
                    
                    if recipient in usernames:
                        target_addr = usernames[recipient]
                        new_header_str = f"FILE_FROM:{sender_name}:{filename}:"
                        new_packet = new_header_str.encode() + file_content
                        server_socket.sendto(new_packet, target_addr)
                        print(f"Routed file '{filename}' from {sender_name} to {recipient}")
                    else:
                        err = f"User '{recipient}' not found.".encode()
                        server_socket.sendto(err, address)
                else:
                    print(f"Invalid file header format from {address}")
            except Exception as e:
                print(f"Error parsing file packet: {e}")
            return

        if message and ":" in message:
            parts = message.split(":", 1)
            if len(parts) == 2:
                recipient = parts[0].strip().strip("<>")
                msg_content = parts[1]
                
                sender_name = clients.get(address, f"Unknown")
                
                if recipient in usernames:
                    target_addr = usernames[recipient]
                    formatted_msg = f"[{sender_name}]: {msg_content}"
                    server_socket.sendto(formatted_msg.encode(), target_addr)
                else:
                    server_socket.sendto(f"User '{recipient}' not found.".encode(), address)
            else:
                 server_socket.sendto("Invalid message format.".encode(), address)
            return
            
    except Exception as e:
        print(f"Error handling packet from {address}: {e}")

def receive():
    print(f"UDP Server is listening on {IP}:{PORT}...")
    while True:
        try:
            data, address = server_socket.recvfrom(BUFFER_SIZE)
            thread = threading.Thread(target=handle_packet, args=(data, address))
            thread.start()
        except Exception as e:
            print(f"Receiver error: {e}")

if __name__ == "__main__":
    receive()
