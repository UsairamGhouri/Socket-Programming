import socket
import threading

# Get user nickname
name = input("Choose your nickname: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 5555))

def receive_messages():
    """Continuously waits for messages from the server."""
    while True:
        try:
            message = client.recv(1024).decode()
            print("\n" + message)
            print("Type your message: ", end="") # Keep the prompt visible
        except:
            print("An error occurred! Disconnecting...")
            client.close()
            break

def send_messages():
    """Wait for user input and send it to the server."""
    while True:
        msg_text = input("Type your message: ")
        full_message = f"{name}: {msg_text}"
        client.send(full_message.encode())

# Start two threads: one to receive, one to send
receive_thread = threading.Thread(target=receive_messages)
receive_thread.start()

send_thread = threading.Thread(target=send_messages)
send_thread.start()