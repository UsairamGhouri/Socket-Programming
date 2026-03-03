import socket
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox, filedialog, ttk
import time
import os
import cv2
import wave
import uuid
import collections
import numpy as np

# Try to import winsound for Windows ringing, otherwise fallback
try:
    import winsound
except ImportError:
    winsound = None

try:
    import pyaudio
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("Warning: PyAudio not found. Calls will not work.")

class ToolTip:
    """
    Creates a tooltip for a given widget as the mouse hovers above it.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
        

    def show_tip(self, event=None):
        if self.tip_window or not self.text: return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 1
        
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class ChatClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

        # --- AUDIO SETUP ---
        self.audio_interface = None
        self.input_stream = None
        if AUDIO_AVAILABLE:
            try:
                self.audio_interface = pyaudio.PyAudio()
                self.input_stream = self.audio_interface.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    input=True,
                    frames_per_buffer=1024,
                    start=False 
                )
            except Exception as e:
                print(f"Audio Device Error: {e}")

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "127.0.0.1"

        self.HOST = simpledialog.askstring("Connect", "Enter Server IP:", initialvalue=local_ip)
        if not self.HOST: exit()
        self.TCP_PORT = 55555
        self.UDP_PORT = 9999
        self.nickname = simpledialog.askstring("Login", "Choose a Nickname:")
        if not self.nickname: exit()

        self.tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            self.tcp_client.connect((self.HOST, self.TCP_PORT))
        except:
            messagebox.showerror("Error", "Could not connect to server.")
            exit()
        
        # --- STATE ---
        self.current_context = 'LOBBY' 
        self.current_context_name = 'Lobby'
        self.groups = {} 
        self.all_online_users = [] 
        self.my_private_chats = set()
        
        self.chat_history = collections.defaultdict(list)
        self.unread_counts = collections.defaultdict(int) 
        
        self.calling_video = False
        self.calling_audio = False
        self.recording_voice = False
        self.tag_popup = None
        self.auto_play_next = False
        
        self.call_window = None 
        # Store call targets explicitly to handle logic correctly
        self.pending_call_target = None
        self.active_call_target = None
        self.pending_call_type = None
        
        # Ringing State
        self.is_ringing = False
        
        # UI State for Hover effects
        self.hide_timers = {}

        self.root.deiconify()
        self.root.title(f"Zen Chat - {self.nickname}")
        self.root.geometry("1100x750")
        
        try:
            icon_image = tk.PhotoImage(file="icon.png")
            self.root.iconphoto(True, icon_image)
        except: pass

        self.build_ui()
        
        threading.Thread(target=self.tcp_listener, daemon=True).start()
        self.udp_client.sendto(f"INIT|{self.nickname}|0|0".encode('utf-8'), (self.HOST, self.UDP_PORT))

    def build_ui(self):
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        self.sidebar = tk.Frame(main_container, width=260, bg="#2c3e50")
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        btn_lobby = tk.Button(self.sidebar, text="🏠 Global Lobby", bg="#34495e", fg="white", font=("Arial", 11, "bold"),
                  command=lambda: self.switch_context('LOBBY', 'Lobby'))
        btn_lobby.pack(fill=tk.X, pady=2)
        ToolTip(btn_lobby, "Join the Public Chat")
        
        tk.Label(self.sidebar, text="MY PRIVATE CHATS", bg="#2c3e50", fg="#bdc3c7", font=("Arial", 8)).pack(fill=tk.X, pady=(15, 2))
        self.private_list_frame = tk.Frame(self.sidebar, bg="#2c3e50")
        self.private_list_frame.pack(fill=tk.X)

        tk.Label(self.sidebar, text="MY GROUPS", bg="#2c3e50", fg="#bdc3c7", font=("Arial", 8)).pack(fill=tk.X, pady=(15, 2))
        self.group_list_frame = tk.Frame(self.sidebar, bg="#2c3e50")
        self.group_list_frame.pack(fill=tk.X)
        
        btn_create = tk.Button(self.sidebar, text="+ Create Group", bg="#27ae60", fg="white", 
                  command=self.create_group_dialog)
        btn_create.pack(fill=tk.X, pady=5)
        ToolTip(btn_create, "Start a new group chat")

        tk.Label(self.sidebar, text="ONLINE IN CURRENT VIEW", bg="#2c3e50", fg="#bdc3c7", font=("Arial", 8)).pack(fill=tk.X, pady=(15, 2))
        self.context_user_frame = tk.Frame(self.sidebar, bg="#2c3e50")
        self.context_user_frame.pack(fill=tk.BOTH, expand=True)

        # Right Area
        right_area = tk.Frame(main_container, bg="white")
        right_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.header_label = tk.Label(right_area, text="Lobby", font=("Arial", 16, "bold"), bg="#ecf0f1", pady=10)
        self.header_label.pack(fill=tk.X)
        
        self.admin_frame = tk.Frame(right_area, bg="#ecf0f1")
        self.admin_frame.pack(fill=tk.X)
        
        self.btn_add_member = tk.Button(self.admin_frame, text="User+", bg="#2980b9", fg="white", command=self.add_member_dialog)
        self.btn_add_member.pack(side=tk.LEFT, padx=5)
        
        self.btn_group_action = tk.Button(self.admin_frame, text="Disband", bg="#c0392b", fg="white", command=self.handle_group_action)
        self.btn_group_action.pack(side=tk.RIGHT, padx=5)

        self.chat_display = scrolledtext.ScrolledText(right_area, state='disabled', font=("Arial", 10), bg="white")
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.chat_display.tag_config('self', foreground='blue')
        self.chat_display.tag_config('system', foreground='gray', font=("Arial", 9, "italic"))
        self.chat_display.tag_config('deleted', foreground='gray', font=("Arial", 10, "italic"))
        self.chat_display.tag_config('notification', foreground='#e67e22', font=("Arial", 10, "bold"))
        
        # Input Area
        input_frame = tk.Frame(right_area, pady=10, bg="white")
        input_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
        
        self.btn_plus = tk.Button(input_frame, text="+", font=("Arial", 14, "bold"), 
                                  bg="#f0f0f0", fg="#555", width=3, relief="flat", cursor="hand2",
                                  command=self.show_attachment_menu)
        self.btn_plus.pack(side=tk.LEFT, padx=(0, 5))
        
        entry_container = tk.Frame(input_frame, bg="white", relief="solid", borderwidth=1)
        entry_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.msg_entry = tk.Entry(entry_container, font=("Arial", 12), relief="flat")
        self.msg_entry.pack(fill=tk.BOTH, expand=True, padx=5, ipady=5)
        self.msg_entry.bind("<Return>", self.send_message)
        self.msg_entry.bind("<KeyRelease>", self.check_tagging)
        
        btn_send = tk.Button(input_frame, text="Send", command=self.send_message, bg="#2980b9", fg="white", font=("Arial", 10, "bold"), relief="flat", padx=15)
        btn_send.pack(side=tk.LEFT, padx=5)
        
        self.switch_context('LOBBY', 'Lobby')

    def show_attachment_menu(self):
        menu = tk.Menu(self.root, tearoff=0, font=("Calibri", 10))
        menu.add_command(label="📞  Audio Call", command=lambda: self.initiate_call_request('AUDIO'))
        menu.add_command(label="🎥  Video Call", command=lambda: self.initiate_call_request('VIDEO'))
        menu.add_command(label="🎤  Voice Message", command=self.start_voice_recording_flow)
        menu.add_separator()
        menu.add_command(label="📄  Document", command=self.send_file)
        x = self.btn_plus.winfo_rootx()
        y = self.btn_plus.winfo_rooty() - 110 
        menu.tk_popup(x, y)

    # --- NETWORK LOGIC ---
    def tcp_listener(self):
        while True:
            try:
                data = self.tcp_client.recv(4096) 
                if not data: break
                try:
                    msg = data.decode('utf-8')
                    self.process_packet(msg)
                except UnicodeDecodeError:
                    if data.startswith(b"FILE_DATA:"):
                        try:
                            header_part = data.split(b':', 2)
                            fname = header_part[1].decode('utf-8')
                            rest = header_part[2]
                            size_str = ""
                            idx = 0
                            for byte in rest:
                                if 48 <= byte <= 57: 
                                    size_str += chr(byte)
                                    idx += 1
                                else: break
                            if size_str:
                                size = int(size_str)
                                self.download_file_data(fname, size, initial_data=rest[idx:])
                        except: pass
            except Exception as e:
                print(f"TCP Error: {e}")
                break

    def process_packet(self, msg):
        if msg.startswith("NICK"):
            self.tcp_client.send(self.nickname.encode('utf-8'))
        elif msg.startswith("USERS:"):
            self.all_online_users = msg[6:].split(',')
            self.root.after(0, self.update_sidebar)
        elif msg.startswith("GROUPS:"):
            raw = msg[7:]
            self.groups = {}
            if raw:
                for item in raw.split(','):
                    parts = item.split(':')
                    if len(parts) >= 3:
                        self.groups[parts[1]] = {'name': parts[0], 'owner': parts[2]}
            self.root.after(0, self.update_sidebar)
        elif msg.startswith("MSG:"):
            parts = msg.split(':', 4)
            if len(parts) == 5:
                self.root.after(0, lambda: self.incoming_message(parts[1], parts[2], parts[3], parts[4]))
        
        # --- CALL HANDLING ---
        elif msg.startswith("CALL_REQUEST:"):
            parts = msg.split(':')
            if len(parts) >= 4:
                call_type = parts[2]
                sender = parts[3]
                self.root.after(0, lambda: self.show_incoming_call_window(sender, call_type))
        
        elif msg.startswith("CALL_ACCEPT:"):
            parts = msg.split(':')
            if len(parts) >= 3:
                acceptor = parts[2]
                self.root.after(0, lambda: self.handle_call_accepted(acceptor))

        elif msg.startswith("CALL_DECLINE:"):
            parts = msg.split(':')
            if len(parts) >= 3:
                decliner = parts[2]
                self.root.after(0, lambda: self.handle_call_declined(decliner))
        
        elif msg.startswith("CALL_CANCEL:"):
            parts = msg.split(':')
            if len(parts) >= 3:
                canceller = parts[2]
                self.root.after(0, lambda: self.handle_call_cancelled(canceller))

        elif msg.startswith("CALL_END:"):
            parts = msg.split(':')
            if len(parts) >= 3:
                ender = parts[2]
                self.root.after(0, lambda: self.handle_call_ended(ender))
        # ---------------------

        elif msg.startswith("DELETE_MSG:"):
            parts = msg.split(':')
            if len(parts) >= 4:
                self.root.after(0, lambda: self.handle_deletion_ui(parts[1], parts[2], parts[3]))
        elif msg.startswith("USER_LEFT:"):
            parts = msg.split(':')
            if len(parts) >= 3:
                self.root.after(0, lambda: self.handle_user_left(parts[1], parts[2]))
        elif msg.startswith("FILE_AVAIL:"):
            parts = msg.split(':')
            self.root.after(0, lambda: self.display_file_link(parts[1], parts[2], parts[3], parts[4], parts[5]))
        elif msg.startswith("FILE_DATA:"):
            parts = msg.split(':')
            self.download_file_data(parts[1], int(parts[2]))

    # --- RINGING LOGIC ---
    def start_ringing(self):
        if self.is_ringing: return
        self.is_ringing = True
        threading.Thread(target=self.ring_loop, daemon=True).start()

    def stop_ringing(self):
        self.is_ringing = False

    def ring_loop(self):
        while self.is_ringing:
            # Try to play a sound
            if winsound:
                # Windows Beep: 1000Hz, 600ms
                winsound.Beep(1000, 600)
                time.sleep(0.2) # Pause between rings
            else:
                # System bell fallback for Mac/Linux
                self.root.bell()
                time.sleep(1.0)

    # --- CHAT NOTIFICATION LOGIC ---
    def add_call_notification(self, context, notification_text):
        """
        Inserts a system-like notification into the chat history and updates badges.
        """
        msg_id = uuid.uuid4().hex
        # Add to history with a special tag
        msg_obj = {
            'msg_id': msg_id,
            'text': f"📞 {notification_text}\n",
            'tags': 'notification', # Using the new tag
            'action': None,
            'sender': 'System',
            'show_bin': False
        }
        self.chat_history[context].append(msg_obj)
        
        # Update unread count if not current context
        if context != self.current_context:
            self.unread_counts[context] += 1
            self.update_sidebar()
            self.root.bell()
        else:
            self.refresh_chat_window()


    # --- CALLING LOGIC ---
    def initiate_call_request(self, call_type):
        if self.current_context == 'LOBBY' or self.current_context in self.groups:
            messagebox.showwarning("Call", "Calls are only available in private chats.")
            return
        
        target = self.current_context
        self.pending_call_type = call_type
        self.pending_call_target = target
        
        # Start ringing (outgoing tone)
        self.start_ringing()
        
        self.show_outgoing_call_window(target, call_type)
        
        msg = f"CALL_REQUEST:{target}:{call_type}:{self.nickname}"
        self.tcp_client.send(msg.encode('utf-8'))

    def show_outgoing_call_window(self, target, call_type):
        if self.call_window: self.call_window.destroy()
        
        self.call_window = tk.Toplevel(self.root)
        self.call_window.title("Calling...")
        self.call_window.geometry("300x200")
        self.call_window.configure(bg="#2c3e50")
        
        tk.Label(self.call_window, text=f"Calling {target}", fg="white", bg="#2c3e50", font=("Arial", 14, "bold")).pack(pady=(40, 10))
        tk.Label(self.call_window, text=f"{call_type} Call...", fg="#bdc3c7", bg="#2c3e50", font=("Arial", 10)).pack()
        
        btn_frame = tk.Frame(self.call_window, bg="#2c3e50")
        btn_frame.pack(side=tk.BOTTOM, pady=20)
        
        tk.Button(btn_frame, text="❌ Cancel", bg="#c0392b", fg="white", width=15, font=("Arial", 10, "bold"),
                  command=self.cancel_call).pack()

    def show_incoming_call_window(self, sender, call_type):
        if self.call_window: self.call_window.destroy()
        
        # Start ringing (incoming tone)
        self.start_ringing()
        
        self.call_window = tk.Toplevel(self.root)
        self.call_window.title("Incoming Call")
        self.call_window.geometry("300x250")
        self.call_window.configure(bg="#2c3e50")
        
        tk.Label(self.call_window, text="Incoming Call", fg="#f39c12", bg="#2c3e50", font=("Arial", 10)).pack(pady=(30, 5))
        tk.Label(self.call_window, text=f"From: {sender}", fg="white", bg="#2c3e50", font=("Arial", 16, "bold")).pack(pady=5)
        tk.Label(self.call_window, text=f"Type: {call_type}", fg="#bdc3c7", bg="#2c3e50", font=("Arial", 10)).pack(pady=(0, 20))
        
        btn_frame = tk.Frame(self.call_window, bg="#2c3e50")
        btn_frame.pack(side=tk.BOTTOM, pady=30, fill=tk.X)
        
        tk.Button(btn_frame, text="✅ Accept", bg="#27ae60", fg="white", width=10, font=("Arial", 10, "bold"),
                  command=lambda: self.accept_call(sender, call_type)).pack(side=tk.LEFT, padx=20)
        
        tk.Button(btn_frame, text="❌ Decline", bg="#c0392b", fg="white", width=10, font=("Arial", 10, "bold"),
                  command=lambda: self.decline_call(sender)).pack(side=tk.RIGHT, padx=20)

    def update_window_to_connected(self, other_user_name):
        if not self.call_window: return
        
        for widget in self.call_window.winfo_children():
            widget.destroy()
            
        # UPDATE TITLE to "Connected with..."
        self.call_window.title(f"Connected with {other_user_name}")
        
        tk.Label(self.call_window, text="Connected", fg="#2ecc71", bg="#2c3e50", font=("Arial", 16, "bold")).pack(pady=(40, 20))
        tk.Label(self.call_window, text=f"with {other_user_name}", fg="#bdc3c7", bg="#2c3e50", font=("Arial", 12)).pack()
        
        tk.Button(self.call_window, text="End Call", bg="#c0392b", fg="white", width=15, font=("Arial", 10, "bold"),
                  command=self.end_call_action).pack(side=tk.BOTTOM, pady=30)

    def accept_call(self, sender, call_type):
        self.stop_ringing()
        self.active_call_target = sender 
        self.update_window_to_connected(sender)
        
        # Inject Notification: "Sender Called You" (Receiver's perspective)
        self.add_call_notification(sender, f"{sender} Called You")
        
        msg = f"CALL_ACCEPT:{sender}:{self.nickname}"
        self.tcp_client.send(msg.encode('utf-8'))
        
        if self.current_context != sender:
            self.switch_context(sender, f"Private: {sender}")
            
        if call_type == 'AUDIO':
            self.start_audio_threads()
        elif call_type == 'VIDEO':
            self.start_video_threads()

    def decline_call(self, sender):
        self.stop_ringing()
        if self.call_window: self.call_window.destroy()
        self.call_window = None
        msg = f"CALL_DECLINE:{sender}:{self.nickname}"
        self.tcp_client.send(msg.encode('utf-8'))

    def cancel_call(self):
        self.stop_ringing()
        if self.call_window: self.call_window.destroy()
        self.call_window = None
        if self.pending_call_target:
            # CHANGED: Send CALL_CANCEL instead of CALL_DECLINE
            msg = f"CALL_CANCEL:{self.pending_call_target}:{self.nickname}"
            self.tcp_client.send(msg.encode('utf-8'))

    def handle_call_accepted(self, acceptor):
        self.stop_ringing()
        self.active_call_target = acceptor 
        self.update_window_to_connected(acceptor)
        
        # Inject Notification: "You Called Acceptor" (Sender's perspective)
        self.add_call_notification(acceptor, f"You Called {acceptor}")
        
        if self.pending_call_type == 'AUDIO':
            self.start_audio_threads()
        elif self.pending_call_type == 'VIDEO':
            self.start_video_threads()

    def handle_call_declined(self, decliner):
        self.stop_ringing()
        if self.call_window: self.call_window.destroy()
        self.call_window = None
        messagebox.showinfo("Call Declined", f"{decliner} has declined your call.")
        self.stop_media_threads()

    def handle_call_cancelled(self, canceller):
        # Simply close everything silently
        self.stop_ringing()
        if self.call_window: self.call_window.destroy()
        self.call_window = None
        self.stop_media_threads()

    def handle_call_ended(self, ender):
        self.stop_ringing() # Just in case
        if self.call_window: self.call_window.destroy()
        self.call_window = None
        messagebox.showinfo("Call Ended", f"{ender} ended the call.")
        self.stop_media_threads()

    def stop_media_threads(self):
        self.calling_audio = False
        self.calling_video = False
        self.active_call_target = None
        cv2.destroyAllWindows()

    def start_audio_threads(self):
        if not AUDIO_AVAILABLE: return
        if self.calling_audio: return
        self.calling_audio = True
        threading.Thread(target=self.audio_sender, daemon=True).start()
        threading.Thread(target=self.audio_receiver, daemon=True).start()

    def start_video_threads(self):
        if self.calling_video: return
        self.calling_video = True
        threading.Thread(target=self.video_sender, daemon=True).start()
        threading.Thread(target=self.video_receiver, daemon=True).start()

    def end_call_action(self):
        self.stop_ringing()
        target = self.active_call_target
        self.stop_media_threads()
        if self.call_window: self.call_window.destroy()
        self.call_window = None
        
        if target:
            msg = f"CALL_END:{target}:{self.nickname}"
            self.tcp_client.send(msg.encode('utf-8'))

    # --- MEDIA THREADS ---
    def video_sender(self):
        try:
            cap = cv2.VideoCapture(0)
            cap.set(3, 320)
            cap.set(4, 240)
            while self.calling_video:
                ret, frame = cap.read()
                if ret:
                    _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 30])
                    header = f"VIDEO|{self.current_context}|0|".encode('utf-8')
                    self.udp_client.sendto(header + buffer, (self.HOST, self.UDP_PORT))
                time.sleep(0.05)
            cap.release()
        except Exception as e:
             print(f"Video Sender Error: {e}")
             self.calling_video = False

    def video_receiver(self):
        try:
            cv2.namedWindow(f"Video Call", cv2.WINDOW_NORMAL)
            while self.calling_video:
                data, _ = self.udp_client.recvfrom(65536)
                parts = data.split(b'|', 3)
                if parts[0] == b'VIDEO':
                    if len(parts) >= 4:
                        img_data = parts[3]
                        np_arr = np.frombuffer(img_data, dtype=np.uint8)
                        frame = cv2.imdecode(np_arr, 1)
                        if frame is not None:
                            cv2.imshow("Video Call", frame)
                            if cv2.waitKey(1) == 27: break
            cv2.destroyAllWindows()
        except Exception as e:
             print(f"Video Receiver Error: {e}")
             self.calling_video = False

    def audio_sender(self):
        try:
            p = self.audio_interface
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=10240, input=True, frames_per_buffer=1024)
            while self.calling_audio:
                data = stream.read(1024)
                header = f"AUDIO|{self.current_context}|0|".encode('utf-8')
                self.udp_client.sendto(header + data, (self.HOST, self.UDP_PORT))
            stream.stop_stream()
            stream.close()
        except: self.calling_audio = False

    def audio_receiver(self):
        try:
            p = self.audio_interface
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=10240, output=True)
            while self.calling_audio:
                data, _ = self.udp_client.recvfrom(4096)
                parts = data.split(b'|', 3)
                if parts[0] == b'AUDIO':
                    if len(parts) >= 4:
                        stream.write(parts[3])
            stream.stop_stream()
            stream.close()
        except: self.calling_audio = False

    # --- REST OF THE LOGIC ---
    def download_file_data(self, filename, size, initial_data=b""):
        if getattr(self, 'auto_play_next', False):
            save_path = f"temp_{uuid.uuid4().hex}_{filename}"
            self.auto_play_next = False
            mode = 'play'
        else:
            save_path = filedialog.asksaveasfilename(initialfile=filename)
            if not save_path: return
            mode = 'save'

        received_len = len(initial_data)
        try:
            with open(save_path, 'wb') as f:
                if initial_data: f.write(initial_data)
                while received_len < size:
                    remaining = size - received_len
                    chunk = self.tcp_client.recv(min(4096, remaining))
                    if not chunk: break
                    f.write(chunk)
                    received_len += len(chunk)
            
            if mode == 'play' and AUDIO_AVAILABLE:
                self.play_audio(save_path)
            elif mode == 'save':
                messagebox.showinfo("Success", f"File saved to {save_path}")
        except Exception as e:
            print(f"Download Failed: {e}")

    def handle_user_left(self, user, context):
        mid = uuid.uuid4().hex
        sys_msg = {'msg_id': mid, 'text': f"⚠️ {user} has left the chat.\n", 'tags': 'system', 'action': None, 'sender': 'System', 'show_bin': False}
        self.chat_history[context].append(sys_msg)
        
        if context == 'LOBBY':
             if user in self.all_online_users: self.all_online_users.remove(user)
             if user in self.my_private_chats:
                 priv_msg = sys_msg.copy()
                 self.chat_history[user].append(priv_msg)
        
        self.update_sidebar()
        if self.current_context == context or self.current_context == user: 
            self.refresh_chat_window()

    # --- Bin Button Logic ---
    
    def create_bin_button(self, msg_id, bg_color="white"):
        btn = tk.Button(self.chat_display, text="🗑", bg=bg_color, fg=bg_color, 
                        activeforeground=bg_color, activebackground=bg_color,
                        font=("Arial", 8), borderwidth=0, cursor="hand2",
                        command=lambda: self.delete_message(msg_id))
        return btn

    def show_bin_icon(self, btn, msg_id):
        if msg_id in self.hide_timers:
            self.root.after_cancel(self.hide_timers[msg_id])
            del self.hide_timers[msg_id]
        current_fg = btn.cget('fg')
        if current_fg != 'red':
            btn.config(fg="gray")

    def schedule_hide_bin_icon(self, btn, msg_id):
        self.hide_timers[msg_id] = self.root.after(100, lambda: self.hide_now(btn))

    def hide_now(self, btn):
        try:
            btn.config(fg="white")
        except: pass

    def on_bin_enter(self, btn, msg_id):
        if msg_id in self.hide_timers:
             self.root.after_cancel(self.hide_timers[msg_id])
             del self.hide_timers[msg_id]
        btn.config(fg="red")

    def on_bin_leave(self, btn, msg_id):
        btn.config(fg="gray")
        self.schedule_hide_bin_icon(btn, msg_id)

    def delete_message(self, msg_id):
        cmd = f"DELETE_MSG:{self.current_context}:{msg_id}"
        self.tcp_client.send(cmd.encode('utf-8'))
        self.handle_deletion_ui(self.current_context, self.nickname, msg_id)

    def handle_deletion_ui(self, target, sender, msg_id):
        if target == 'LOBBY' or target in self.groups:
            context = target
        elif target == self.nickname: 
            context = sender
        else: 
            context = target
        history = self.chat_history[context]
        new_history = []
        replaced = False
        for msg_data in history:
            if msg_data['msg_id'] == msg_id:
                if not replaced:
                    del_text = "You deleted this message" if sender == self.nickname else f"{sender} deleted this message"
                    new_history.append({'msg_id': msg_id, 'text': f"{del_text}\n", 'tags': 'deleted', 'action': None, 'sender': sender, 'show_bin': False})
                    replaced = True
            else:
                new_history.append(msg_data)
        self.chat_history[context] = new_history
        if self.current_context == context:
            self.refresh_chat_window()

    def refresh_chat_window(self):
        self.chat_display.config(state='normal')
        self.chat_display.delete(1.0, tk.END)
        for timer_id in self.hide_timers.values():
            self.root.after_cancel(timer_id)
        self.hide_timers.clear()
        history = self.chat_history[self.current_context]
        for msg_data in history:
            text = msg_data.get('text', '')
            tags = msg_data.get('tags', '')
            action = msg_data.get('action', None)
            msg_id = msg_data.get('msg_id', None)
            sender = msg_data.get('sender', '')
            show_bin = msg_data.get('show_bin', False)
            if not text and not action and not show_bin: continue
            has_newline = text.endswith('\n')
            clean_text = text.rstrip('\n')
            msg_tag = f"msg_{msg_id}" if msg_id else "unknown"
            if tags:
                self.chat_display.insert(tk.END, clean_text, (tags, msg_tag))
            else:
                self.chat_display.insert(tk.END, clean_text, msg_tag)
            if action: self.render_button(action)
            if show_bin and msg_id and sender == self.nickname and 'deleted' not in tags:
                bin_btn = self.create_bin_button(msg_id, bg_color="white")
                self.chat_display.window_create(tk.END, window=bin_btn, padx=5)
                self.chat_display.tag_bind(msg_tag, "<Enter>", lambda e, b=bin_btn, m=msg_id: self.show_bin_icon(b, m))
                self.chat_display.tag_bind(msg_tag, "<Leave>", lambda e, b=bin_btn, m=msg_id: self.schedule_hide_bin_icon(b, m))
                bin_btn.bind("<Enter>", lambda e, b=bin_btn, m=msg_id: self.on_bin_enter(b, m))
                bin_btn.bind("<Leave>", lambda e, b=bin_btn, m=msg_id: self.on_bin_leave(b, m))
            if has_newline:
                self.chat_display.insert(tk.END, '\n')
        self.chat_display.config(state='disabled')
        self.chat_display.yview(tk.END)

    def render_button(self, action):
        fid = action.split(":", 1)[1]
        if action.startswith("DL:"):
            btn = tk.Button(self.chat_display, text="⬇ Download", bg="#27ae60", fg="white", 
                            font=("Arial", 8, "bold"), cursor="hand2",
                            command=lambda f=fid: self.request_download(f))
            ToolTip(btn, "Download this file")
        elif action.startswith("PLAY:"):
            btn = tk.Button(self.chat_display, text="▶ Play Audio", bg="#e74c3c", fg="white", 
                            font=("Arial", 8, "bold"), cursor="hand2",
                            command=lambda f=fid: self.request_download(f, auto_play=True))
            ToolTip(btn, "Listen to voice message")
        self.chat_display.window_create(tk.END, window=btn, padx=5, pady=2)

    def switch_context(self, context_id, context_name):
        self.unread_counts[context_id] = 0
        self.current_context = context_id
        self.current_context_name = context_name
        self.header_label.config(text=f"{context_name}")
        self.update_admin_buttons()
        self.update_sidebar() 
        self.refresh_chat_window()

    def update_admin_buttons(self):
        self.admin_frame.pack_forget()
        if self.current_context == 'LOBBY' or self.current_context in self.all_online_users: return
        if self.current_context in self.groups:
            self.admin_frame.pack(fill=tk.X)
            info = self.groups[self.current_context]
            if info['owner'] == self.nickname:
                self.btn_add_member.pack(side=tk.LEFT, padx=5)
                self.btn_group_action.config(text="Disband Group", bg="#c0392b")
            else:
                self.btn_add_member.pack_forget() 
                self.btn_group_action.config(text="Leave Group", bg="#f39c12")

    def update_sidebar(self):
        for widget in self.private_list_frame.winfo_children(): widget.destroy()
        for user in self.my_private_chats:
            count = self.unread_counts[user]
            txt, col = (f"👤 {user} 🔴({count})", "#ff6b6b") if count > 0 else (f"👤 {user}", "white")
            btn = tk.Button(self.private_list_frame, text=txt, bg="#34495e", fg=col, anchor="w",
                      command=lambda u=user: self.switch_context(u, f"Private: {u}"))
            btn.pack(fill=tk.X, padx=2, pady=1)
            ToolTip(btn, f"Chat with {user}")

        for widget in self.group_list_frame.winfo_children(): widget.destroy()
        for gid, info in self.groups.items():
            count = self.unread_counts[gid]
            txt, col = (f"# {info['name']} 🔴({count})", "#ff6b6b") if count > 0 else (f"# {info['name']}", "white")
            btn = tk.Button(self.group_list_frame, text=txt, bg="#34495e", fg=col, anchor="w",
                      command=lambda g=gid, n=info['name']: self.switch_context(g, n))
            btn.pack(fill=tk.X, padx=2, pady=1)
            ToolTip(btn, f"Enter {info['name']}")
            
        self.update_context_users()

    def update_context_users(self):
        for widget in self.context_user_frame.winfo_children(): widget.destroy()
        if self.current_context == 'LOBBY':
            for user in self.all_online_users:
                if user != self.nickname:
                    count = self.unread_counts[user]
                    display_txt, fg_col = (f"🔴 {user} ({count})", "#ff6b6b") if count > 0 else (f"🟢 {user}", "white")
                    btn = tk.Button(self.context_user_frame, text=display_txt, bg="#2c3e50", fg=fg_col, anchor="w",
                              command=lambda u=user: self.initiate_private_chat(u))
                    btn.pack(fill=tk.X)
                    ToolTip(btn, "Start Private Chat")
        elif self.current_context in self.all_online_users:
             tk.Label(self.context_user_frame, text=f"🟢 {self.current_context}", bg="#2c3e50", fg="white").pack(fill=tk.X)

    def initiate_private_chat(self, user):
        self.my_private_chats.add(user)
        self.update_sidebar()
        self.switch_context(user, f"Private: {user}")

    def send_message(self, event=None):
        text = self.msg_entry.get()
        if not text: return
        self.msg_entry.delete(0, tk.END)
        msg_id = uuid.uuid4().hex
        msg = f"MSG:{self.current_context}:{self.nickname}:{msg_id}:{text}"
        self.tcp_client.send(msg.encode('utf-8'))
        self.incoming_message(self.current_context, self.nickname, msg_id, text)

    def incoming_message(self, context, sender, msg_id, content):
        effective_context = context
        if context == self.nickname: 
            effective_context = sender
            if sender not in self.my_private_chats:
                self.my_private_chats.add(sender)
        
        # Check for disband command embedded in message
        if "Group disbanded" in content and "Server" in sender:
            if context in self.groups:
                del self.groups[context]
                self.update_sidebar()
                if self.current_context == context:
                    self.switch_context('LOBBY', 'Lobby')
                    messagebox.showinfo("Info", "This group has been disbanded by the owner.")
                return

        if any(m['msg_id'] == msg_id for m in self.chat_history[effective_context]): return

        display_text = f"You: {content}\n" if sender == self.nickname else f"{sender}: {content}\n"
        tag = 'self' if sender == self.nickname else ''
        
        msg_obj = {'msg_id': msg_id, 'text': display_text, 'tags': tag, 'action': None, 'sender': sender, 'show_bin': True}
        self.chat_history[effective_context].append(msg_obj)

        if effective_context != self.current_context:
            self.unread_counts[effective_context] += 1
            self.update_sidebar()
            self.root.bell()
        elif effective_context == self.current_context:
            self.refresh_chat_window()

    def display_file_link(self, context, sender, filename, file_id, msg_id):
        effective_context = context
        if context == self.nickname: effective_context = sender
        msg_text = f"{sender} sent file: {filename} "
        self.chat_history[effective_context].append({'msg_id': msg_id, 'text': msg_text, 'tags': '', 'action': None, 'sender': sender, 'show_bin': False})
        self.chat_history[effective_context].append({'msg_id': msg_id, 'text': '', 'tags': '', 'action': f"DL:{file_id}", 'sender': sender, 'show_bin': False})
        if filename.endswith('.wav'):
             self.chat_history[effective_context].append({'msg_id': msg_id, 'text': '', 'tags': '', 'action': f"PLAY:{file_id}", 'sender': sender, 'show_bin': False})
        self.chat_history[effective_context].append({'msg_id': msg_id, 'text': "\n", 'tags': '', 'action': None, 'sender': sender, 'show_bin': True})

        if effective_context != self.current_context:
            self.unread_counts[effective_context] += 1
            self.update_sidebar()
            self.root.bell()
        elif effective_context == self.current_context:
            self.refresh_chat_window()

    def request_download(self, fid, auto_play=False):
        self.auto_play_next = auto_play 
        self.tcp_client.send(f"FILE_DOWNLOAD:{fid}".encode('utf-8'))

    def play_audio(self, filepath):
        def _play():
            try:
                wf = wave.open(filepath, 'rb')
                p = self.audio_interface or pyaudio.PyAudio()
                stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                                channels=wf.getnchannels(),
                                rate=wf.getframerate(),
                                output=True)
                data = wf.readframes(1024)
                while data:
                    stream.write(data)
                    data = wf.readframes(1024)
                stream.stop_stream()
                stream.close()
                os.remove(filepath)
            except Exception as e:
                print(f"Playback error: {e}")
        threading.Thread(target=_play, daemon=True).start()

    def start_voice_recording_flow(self):
        if not AUDIO_AVAILABLE: return
        if self.recording_voice: return
        self.recording_voice = True
        self.btn_plus.config(text="🛑", bg="#e74c3c", fg="white", command=self.stop_voice_recording_flow)
        threading.Thread(target=self.record_loop, daemon=True).start()

    def stop_voice_recording_flow(self):
        self.recording_voice = False
        self.btn_plus.config(text="+", bg="#f0f0f0", fg="#555", command=self.show_attachment_menu)

    def record_loop(self):
        p = self.audio_interface
        if not p: return
        if self.input_stream:
            stream = self.input_stream
            stream.start_stream()
        else:
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        frames = []
        while self.recording_voice:
            try:
                data = stream.read(1024, exception_on_overflow=False)
                frames.append(data)
            except: break
        stream.stop_stream()
        if stream != self.input_stream: stream.close()
        
        filename = f"voice_{int(time.time())}.wav"
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        filesize = os.path.getsize(filename)
        header = f"FILE_UPLOAD:{self.current_context}:{filename}:{filesize}:{self.nickname}"
        try:
            self.tcp_client.send(header.encode('utf-8'))
            time.sleep(0.2)
            with open(filename, 'rb') as f:
                self.tcp_client.sendall(f.read())
        except Exception as e:
            print(f"Upload Error: {e}")
        os.remove(filename)

    def create_group_dialog(self):
        name = simpledialog.askstring("Group", "Enter Group Name:")
        if name: self.tcp_client.send(f"CREATE_GROUP:{name}:{self.nickname}".encode('utf-8'))

    def add_member_dialog(self):
        top = tk.Toplevel(self.root)
        top.title("Add Member")
        lb = tk.Listbox(top)
        lb.pack(fill=tk.BOTH, expand=True)
        for u in self.all_online_users:
            if u != self.nickname:
                lb.insert(tk.END, u)
        def do_add():
            user = lb.get(tk.ACTIVE)
            if user:
                self.tcp_client.send(f"ADD_MEMBER:{self.current_context}:{user}:{self.nickname}".encode('utf-8'))
                top.destroy()
        tk.Button(top, text="Add Selected", command=do_add).pack()
        
    def handle_group_action(self):
        action = self.btn_group_action.cget('text')
        cmd = "LEAVE_GROUP"
        if action == "Disband Group":
             if not messagebox.askyesno("Confirm", "Disband this group?"): return
             # Also remove locally for owner
             if self.current_context in self.groups:
                 del self.groups[self.current_context]
                 self.update_sidebar()
                 # Defer switch to avoid glitches
                 self.root.after(100, lambda: self.switch_context('LOBBY', 'Lobby'))
        else:
             if not messagebox.askyesno("Confirm", "Leave this group?"): return
             # Remove locally for member
             if self.current_context in self.groups:
                 del self.groups[self.current_context]
                 self.update_sidebar()
                 self.root.after(100, lambda: self.switch_context('LOBBY', 'Lobby'))
                 
        self.tcp_client.send(f"{cmd}:{self.current_context}:{self.nickname}".encode('utf-8'))

    def check_tagging(self, event):
        text = self.msg_entry.get()
        if not text: return
        cursor_pos = self.msg_entry.index(tk.INSERT)
        if cursor_pos > 0 and text[cursor_pos-1] == '@':
            self.show_tag_popup()
        elif self.tag_popup:
            self.tag_popup.destroy()
            self.tag_popup = None

    def show_tag_popup(self):
        if self.tag_popup: self.tag_popup.destroy()
        self.tag_popup = tk.Toplevel(self.root)
        self.tag_popup.wm_overrideredirect(True)
        x = self.msg_entry.winfo_rootx()
        y = self.msg_entry.winfo_rooty() - 100
        self.tag_popup.geometry(f"150x100+{x}+{y}")
        lb = tk.Listbox(self.tag_popup)
        lb.pack(fill=tk.BOTH, expand=True)
        for user in self.all_online_users: lb.insert(tk.END, user)
        lb.bind("<Double-Button-1>", lambda e: self.insert_tag(lb.get(tk.ACTIVE)))
        lb.bind("<Return>", lambda e: self.insert_tag(lb.get(tk.ACTIVE)))

    def insert_tag(self, user):
        self.msg_entry.insert(tk.INSERT, f"{user} ")
        self.tag_popup.destroy()
        self.tag_popup = None
        self.msg_entry.focus()
        
    def send_file(self):
        filepath = filedialog.askopenfilename()
        if not filepath: return
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)
        header = f"FILE_UPLOAD:{self.current_context}:{filename}:{filesize}:{self.nickname}"
        try:
            self.tcp_client.send(header.encode('utf-8'))
            time.sleep(0.1)
            with open(filepath, 'rb') as f:
                self.tcp_client.sendall(f.read())
        except: pass

    def start(self):
        self.root.mainloop()

if __name__ == "__main__":
    ChatClient().start()