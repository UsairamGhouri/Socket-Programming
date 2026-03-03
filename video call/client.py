import socket
import cv2
import pickle
import struct
import threading

# Connection setup
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 7777))

# Registration
client.recv(1024)
my_email = input("Your Email: ")
client.send(my_email.encode())
target_email = input("Target Email to Call: ")

def send_video():
    cap = cv2.VideoCapture(0) # Open Webcam
    while True:
        ret, frame = cap.read()
        # Resize for faster transmission
        frame = cv2.resize(frame, (320, 240))
        # Serialize the frame (convert to bytes)
        data = pickle.dumps(frame)
        
        # Create header: [TargetEmail(20 bytes)][DataSize(8 bytes)]
        header = target_email.ljust(20).encode() + struct.pack(">Q", len(data))
        
        try:
            client.sendall(header + data)
        except:
            break
    cap.release()

def receive_video():
    data = b""
    payload_size = struct.calcsize(">Q") # Size of the 'Q' (unsigned long long)
    
    while True:
        try:
            # Get the size of the incoming frame
            while len(data) < payload_size:
                data += client.recv(4096)
            
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">Q", packed_msg_size)[0]

            # Get the actual frame data
            while len(data) < msg_size:
                data += client.recv(4096)
            
            frame_data = data[:msg_size]
            data = data[msg_size:]

            # Convert bytes back to an image and show it
            frame = pickle.loads(frame_data)
            cv2.imshow('Incoming Video Call', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except:
            break
    cv2.destroyAllWindows()

# Start both sending and receiving
threading.Thread(target=send_video).start()
threading.Thread(target=receive_video).start()