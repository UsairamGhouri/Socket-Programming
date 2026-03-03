import socket
import threading

HOST = '127.0.0.1'
PORT = 9999
clients = {} # {email: socket}

def handle_audio(conn, addr):
    try:
        # Register user
        conn.send("REG".encode())
        email = conn.recv(1024).decode()
        clients[email] = conn
        print(f"[AUDIO SERVER] {email} connected for calling.")

        while True:
            # Receive audio data from sender
            # Format: [TargetEmail(20 bytes)][AudioData]
            data = conn.recv(4096)
            if not data: break

            # For simplicity, we assume the first 20 bytes is the recipient's email
            target_email = data[:20].decode().strip()
            audio_chunk = data[20:]

            if target_email in clients:
                # Forward only the audio chunk to the target
                clients[target_email].send(audio_chunk)
    except:
        pass

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
print("Audio Server is waiting for calls...")

while True:
    c, a = server.accept()
    threading.Thread(target=handle_audio, args=(c, a)).start()