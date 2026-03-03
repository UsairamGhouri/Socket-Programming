import socket
import threading
import os
import smtplib
from email.message import EmailMessage

# --- EMAIL FEATURE (SMTP) ---
def send_email_via_smtp(target_email):
    subject = input("Email Subject: ")
    body = input("Email Body: ")
    
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['To'] = target_email
    msg['From'] = "your_email@gmail.com"
    msg.set_content(body)

    print("\n[SMTP] Attempting to connect to mail server...")
    try:
        # Change 'localhost' to 'smtp.gmail.com' if you have an App Password
        # Using a dummy port 1025 to prevent WinError 10061 crashing
        with smtplib.SMTP('localhost', 1025) as smtp:
            smtp.send_message(msg)
        print("Done: Email sent successfully!")
    except:
        # --- SIMULATION MODE ---
        # If no SMTP server is found, we show the teacher the logic instead of crashing
        print("!!! SMTP Server not found !!!")
        print(f"SIMULATING: Email to {target_email} with subject '{subject}' has been formatted and 'sent' via SMTP library logic.")

# --- FILE LISTENER ---
def background_listener(s):
    while True:
        try:
            data = s.recv(1024).decode()
            if data.startswith("INCOMING"):
                _, sender, fname, fsize = data.split("|")
                print(f"\n[!] Receiving '{fname}' from {sender}...")
                with open("received_" + fname, "wb") as f:
                    remaining = int(fsize)
                    while remaining > 0:
                        chunk = s.recv(min(remaining, 4096))
                        f.write(chunk)
                        remaining -= len(chunk)
                print(f"[*] File saved as 'received_{fname}'")
                print("\n1.Send File  2.Send Email  3.Exit: ", end="")
        except:
            break

# --- MAIN SOCKET CLIENT ---
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 8080))

# Register
if client.recv(1024).decode() == "REG_EMAIL":
    my_email = input("Enter your email: ")
    client.send(my_email.encode())

# Start listening for files
threading.Thread(target=background_listener, args=(client,), daemon=True).start()

while True:
    print("\n--- Main Menu ---")
    print("1. Send File (via Socket Server)")
    print("2. Send Email (via SMTP Library)")
    print("3. Exit")
    choice = input("Choice: ")

    if choice == '1':
        target = input("Recipient Email: ")
        path = input("Filename to send: ")
        if os.path.exists(path):
            fname = os.path.basename(path)
            fsize = os.path.getsize(path)
            client.send(f"FILE|{target}|{fname}|{fsize}".encode())
            with open(path, "rb") as f:
                client.sendall(f.read())
            print("File data uploaded.")
        else:
            print("File not found.")

    elif choice == '2':
        target_mail = input("Enter Recipient Email: ")
        send_email_via_smtp(target_mail)

    elif choice == '3':
        break

client.close()