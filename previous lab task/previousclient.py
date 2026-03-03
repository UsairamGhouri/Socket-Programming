import socket
import smtplib
import os
from email.message import EmailMessage

# Settings
IP = "127.0.0.1"
PORT = 8080
BUFFER_SIZE = 1024

def send_email_feature():
    print("\n--- Email Feature ---")
    receiver = input("Enter recipient email: ")
    cc_email = input("Enter CC email (or leave blank): ")
    filepath = input("Enter the path of the file to attach: ")

    if not os.path.exists(filepath):
        print("Error: File not found!")
        return

    # Set up email
    msg = EmailMessage()
    msg['Subject'] = "File Share via Python App"
    msg['From'] = "your_email@gmail.com" # Put your email here
    msg['To'] = receiver
    if cc_email:
        msg['Cc'] = cc_email
    msg.set_content("Please find the attached file.")

    # Read and attach file
    with open(filepath, 'rb') as f:
        file_data = f.read()
        file_name = os.path.basename(filepath)
        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)

    try:
        # Note: For Gmail, you need an "App Password"
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login("your_email@gmail.com", "your_app_password") 
            smtp.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((IP, PORT))
    except:
        print("Could not connect to server.")
        return

    name = input("Enter your name: ")
    client.send(name.encode())

    while True:
        print("\n1. Send File to Client\n2. Send Email\n3. Exit")
        choice = input("Select an option: ")

        if choice == '1':
            recipient = input("Enter recipient name: ")
            filename = input("Enter filename to send: ")
            if os.path.exists(filename):
                with open(filename, 'rb') as f:
                    data = f.read()
                header = f"SEND_FILE|{recipient}|{filename}"
                client.send(header.encode())
                client.send(data)
                print(client.recv(BUFFER_SIZE).decode()) # Wait for ack
            else:
                print("File does not exist.")
        
        elif choice == '2':
            send_email_feature()
            
        elif choice == '3':
            break

    client.close()

if __name__ == "__main__":
    start_client()