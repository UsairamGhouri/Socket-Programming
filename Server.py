import socket
import threading
import time
import uuid

# --- CONFIGURATION ---
HOST = '0.0.0.0'
TCP_PORT = 55555
UDP_PORT = 9999

# --- DATA STRUCTURES ---
clients = {}      # {socket: username}
usernames = {}    # {username: socket}
udp_map = {}      # {username: (ip, port)}

# Room Structure:
groups = {} 
# {gid: {'owner': user, 'members': [], 'name': name}}

# File Storage
file_storage = {}

# --- SERVER SETUP ---
tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_server.bind((HOST, TCP_PORT))
tcp_server.listen()

udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_server.bind((HOST, UDP_PORT))

# --- HELPER FUNCTIONS ---

def send_to_user(username, message):
    if username in usernames:
        try:
            usernames[username].send(message.encode('utf-8'))
        except: pass

def broadcast_to_group(group_id, message, exclude_user=None):
    if group_id == 'LOBBY':
        for sock, user in clients.items():
            if user != exclude_user:
                try: sock.send(message.encode('utf-8'))
                except: pass
    elif group_id in groups:
        members = groups[group_id]['members']
        for member in members:
            if member != exclude_user:
                send_to_user(member, message)

def update_user_lists(target_socket=None):
    """Sends the list of ONLINE USERS only."""
    all_users = list(usernames.keys())
    user_str = "USERS:" + ",".join(all_users)
    
    if target_socket:
        try: target_socket.send(user_str.encode('utf-8'))
        except: pass
    else:
        for sock in clients:
            try: sock.send(user_str.encode('utf-8'))
            except: pass

def sync_groups(username):
    """Sends the list of GROUPS a user belongs to."""
    if username not in usernames: return
    sock = usernames[username]
    
    my_groups = []
    for gid, info in groups.items():
        if username in info['members']:
            my_groups.append(f"{info['name']}:{gid}:{info['owner']}")
    
    msg = "GROUPS:" + ",".join(my_groups)
    try: sock.send(msg.encode('utf-8'))
    except: pass

def handle_tcp_client(client):
    username = None
    try:
        client.send("NICK".encode('utf-8'))
        username = client.recv(1024).decode('utf-8')
        
        if username in usernames:
            client.send("ERR:Username taken".encode('utf-8'))
            client.close()
            return

        clients[client] = username
        usernames[username] = client
        print(f"[NEW TCP] {username} connected.")
        client.send("OK:Welcome".encode('utf-8'))
        
        update_user_lists() 
        sync_groups(username)
        
        broadcast_to_group('LOBBY', f"MSG:LOBBY:Server:{uuid.uuid4().hex}:User {username} joined!", exclude_user=username)

        while True:
            message = client.recv(1024 * 1024)
            if not message: break
            
            try:
                msg_str = message.decode('utf-8')
            except:
                continue

            # --- MESSAGE HANDLING ---
            if msg_str.startswith("MSG:"):
                # PROTOCOL: MSG:TargetID:Sender:MsgID:Content
                parts = msg_str.split(':', 4)
                if len(parts) == 5:
                    _, target, sender, msg_id, content = parts
                    if target == 'LOBBY':
                        broadcast_to_group('LOBBY', msg_str) 
                    elif target in groups:
                        broadcast_to_group(target, msg_str)
                    elif target in usernames:
                        send_to_user(target, msg_str)
            
            # --- CALL SIGNALING ---
            elif msg_str.startswith("CALL_"):
                parts = msg_str.split(':')
                if len(parts) >= 3:
                    target = parts[1]
                    if target in usernames:
                        send_to_user(target, msg_str)

            # --- DELETE MESSAGE ---
            elif msg_str.startswith("DELETE_MSG:"):
                try:
                    _, target, msg_id = msg_str.split(':')
                    del_cmd = f"DELETE_MSG:{target}:{username}:{msg_id}"
                    
                    if target == 'LOBBY':
                        broadcast_to_group('LOBBY', del_cmd)
                    elif target in groups:
                        broadcast_to_group(target, del_cmd)
                    elif target in usernames:
                        send_to_user(target, del_cmd)
                except:
                    pass
                    
            # --- GROUP LOGIC ---
            elif msg_str.startswith("CREATE_GROUP:"):
                _, g_name, owner = msg_str.split(':')
                g_id = str(uuid.uuid4())[:8]
                groups[g_id] = {'owner': owner, 'members': [owner], 'name': g_name}
                sync_groups(owner)

            elif msg_str.startswith("ADD_MEMBER:"):
                _, g_id, new_user, requestor = msg_str.split(':')
                if g_id in groups and groups[g_id]['owner'] == requestor:
                    if new_user in usernames and new_user not in groups[g_id]['members']:
                        groups[g_id]['members'].append(new_user)
                        sync_groups(new_user)
                        sys_id = uuid.uuid4().hex
                        broadcast_to_group(g_id, f"MSG:{g_id}:Server:{sys_id}:{new_user} was added.")

            elif msg_str.startswith("LEAVE_GROUP:"):
                _, g_id, user = msg_str.split(':')
                if g_id in groups:
                    if user == groups[g_id]['owner']:
                        sys_id = uuid.uuid4().hex
                        broadcast_to_group(g_id, f"MSG:{g_id}:Server:{sys_id}:Group disbanded.")
                        members = groups[g_id]['members']
                        del groups[g_id]
                        for m in members: sync_groups(m)
                    elif user in groups[g_id]['members']:
                        groups[g_id]['members'].remove(user)
                        sys_id = uuid.uuid4().hex
                        broadcast_to_group(g_id, f"MSG:{g_id}:Server:{sys_id}:{user} left.")
                        sync_groups(user)

            # --- FILE TRANSFER ---
            elif msg_str.startswith("FILE_UPLOAD:"):
                _, target, fname, size, sender = msg_str.split(':')
                size = int(size)
                file_data = b""
                remaining = size
                while remaining > 0:
                    chunk = client.recv(min(4096, remaining))
                    if not chunk: break
                    file_data += chunk
                    remaining -= len(chunk)
                
                fid = str(uuid.uuid4())[:8]
                file_storage[fid] = {'filename': fname, 'data': file_data, 'sender': sender}
                
                msg_id = uuid.uuid4().hex
                notification = f"FILE_AVAIL:{target}:{sender}:{fname}:{fid}:{msg_id}"
                
                if target == 'LOBBY': broadcast_to_group('LOBBY', notification)
                elif target in groups: broadcast_to_group(target, notification)
                elif target in usernames:
                    # Send to Receiver
                    send_to_user(target, notification)
                    # ALSO Send to Sender (so they get the preview/buttons)
                    client.send(notification.encode('utf-8'))

            elif msg_str.startswith("FILE_DOWNLOAD:"):
                _, fid = msg_str.split(':')
                if fid in file_storage:
                    finfo = file_storage[fid]
                    header = f"FILE_DATA:{finfo['filename']}:{len(finfo['data'])}"
                    client.send(header.encode('utf-8'))
                    time.sleep(0.1)
                    client.sendall(finfo['data'])

    except Exception as e:
        print(f"TCP Error {username}: {e}")
    finally:
        if username:
            # Remove user from active lists
            if username in usernames: del usernames[username]
            if client in clients: del clients[client]
            
            update_user_lists()
            
            sys_id = uuid.uuid4().hex
            # Notify Lobby that user left (Persistent 'who left' history)
            broadcast_to_group('LOBBY', f"USER_LEFT:{username}:LOBBY")
            
            # Handle Groups: Remove Member OR Disband if Owner
            # Use list(groups.keys()) to safely modify dictionary while iterating
            for gid in list(groups.keys()):
                info = groups[gid]
                
                if info['owner'] == username:
                    # Case 1: Owner Left -> Disband Group
                    disband_msg = f"MSG:{gid}:Server:{sys_id}:Owner disconnected. Group disbanded."
                    
                    # Notify all members
                    for member in info['members']:
                        if member != username:
                            send_to_user(member, disband_msg)
                    
                    # Delete the group
                    del groups[gid]
                    
                    # Update sidebar for remaining members
                    for member in info['members']:
                        if member != username:
                            sync_groups(member)
                            
                elif username in info['members']:
                    # Case 2: Member Left -> Notify Group
                    info['members'].remove(username)
                    broadcast_to_group(gid, f"USER_LEFT:{username}:{gid}")

def handle_udp():
    print(f"UDP Server listening on {HOST}:{UDP_PORT}")
    while True:
        try:
            data, addr = udp_server.recvfrom(60000)
            parts = data.split(b'|', 3)
            
            if parts[0] == b'INIT':
                u_name = parts[1].decode('utf-8')
                udp_map[u_name] = addr
                continue
            
            # --- FIX: Allow 3 parts (Type|Target|Data) ---
            if len(parts) < 3: continue 
            target = parts[1].decode('utf-8')
            
            if target in udp_map:
                udp_server.sendto(data, udp_map[target])
            elif target in groups:
                members = groups[target]['members']
                for member in members:
                    if member in udp_map:
                         udp_server.sendto(data, udp_map[member])
        except: pass

if __name__ == "__main__":
    threading.Thread(target=handle_udp, daemon=True).start()
    print(f"TCP Server running on {HOST}:{TCP_PORT}")
    while True:
        client, addr = tcp_server.accept()
        threading.Thread(target=handle_tcp_client, args=(client,), daemon=True).start()