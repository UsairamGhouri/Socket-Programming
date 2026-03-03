import socket
import os
import threading

def receive_notifications(s):
    """Listens for incoming alerts from the server."""
    while True:
        try:
            msg = s.recv(1024).decode()
            if msg:
                print(msg)
                print("\nChoice (1:Email, 2:Exit): ", end="")
        except:
            break

# Connect to Server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 12345))

# Registration
reg_msg = s.recv(1024).decode()
my_email = input(reg_msg)
s.send(my_email.encode())

# Start a thread to hear notifications while typing
threading.Thread(target=receive_notifications, args=(s,), daemon=True).start()

while True:
    print("\n--- System Menu ---")
    print("1. Send Email to another client")
    print("2. Exit")
    choice = input("Choice: ")

    if choice == '1':
        target = input("Recipient Email: ")
        subj = input("Subject: ")
        body = input("Message Body: ")
        
        # We send the "Email" via the existing Socket connection
        # No SMTP server needed, so no WinError 10061!
        payload = f"SEND_MAIL|{target}|{subj}|{body}"
        s.send(payload.encode())
        
        # Wait for confirmation
        response = s.recv(1024).decode()
        if "MAIL_SUCCESS" in response:
            print("Server confirmed: Email delivered to recipient's mailbox.")
        
    elif choice == '2':
        break

s.close()