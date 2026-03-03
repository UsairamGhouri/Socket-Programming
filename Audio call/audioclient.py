import socket
import threading
import pyaudio

# Audio Settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

p = pyaudio.PyAudio()

# Setup Microphone (Stream for recording)
stream_in = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

# Setup Speakers (Stream for playing)
stream_out = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 9999))

# Register
client.recv(1024)
my_email = input("Enter your email to start audio service: ")
client.send(my_email.encode())

target_email = input("Enter the email of the person you want to call: ")

def send_mic_data():
    print("--- Call Started (Mic Active) ---")
    while True:
        try:
            # Read from mic
            raw_data = stream_in.read(CHUNK)
            # Add target email as header (padded to 20 chars)
            header = target_email.ljust(20).encode()
            client.sendall(header + raw_data)
        except:
            break

def receive_speaker_data():
    print("--- Listening for Incoming Audio ---")
    while True:
        try:
            # Receive audio chunk and play it
            audio_data = client.recv(CHUNK * 2) # Audio data is usually double the chunk size in bytes
            stream_out.write(audio_data)
        except:
            break

# Start threads
threading.Thread(target=send_mic_data).start()
threading.Thread(target=receive_speaker_data).start()