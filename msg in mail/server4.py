import socket
import threading
import os

HOST = '127.0.0.1'
PORT = 12345

# Dictionary to keep track of online clients {email: socket}
online_users = {}

# Create a folder to store emails if it doesn't exist
if not os.path.exists("mailbox"):
    os.makedirs("mailbox")

def handle_client(conn, addr):
    try:
        # Step 1: Register the client
        conn.send("Enter your email to register: ".encode())
        user_email = conn.recv(1024).decode()
        online_users[user_email] = conn
        print(f"[REGISTERED] {user_email} is now online.")

        while True:
            # Wait for instruction
            data = conn.recv(1024).decode()
            if not data: break

            # Format: SEND_MAIL|recipient|subject|body
            if data.startswith("SEND_MAIL"):
                _, recipient, subject, body = data.split("|")
                
                # Create the email content
                email_content = f"From: {user_email}\nSubject: {subject}\n\n{body}"
                
                # Save the "Email" as a file on the server
                file_path = f"mailbox/{recipient}.txt"
                with open(file_path, "a") as f:
                    f.write(email_content + "\n" + "-"*20 + "\n")
                
                # If recipient is online, notify them immediately
                if recipient in online_users:
                    online_users[recipient].send(f"\n[NOTIFICATION] You have a new mail from {user_email}!".encode())
                
                conn.send("MAIL_SUCCESS".encode())

    except:
        pass
    finally:
        conn.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
print("Server is running... waiting for clients.")

while True:
    c, a = server.accept()
    threading.Thread(target=handle_client, args=(c, a)).start()