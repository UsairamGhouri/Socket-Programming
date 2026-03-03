Socket Programming Project
==========================

This repository contains a comprehensive collection of Python scripts demonstrating various concepts and applications of socket programming. The project covers communication protocols (TCP and UDP), real-time multimedia streaming, and simulated mail services.

Features
--------

### 1\. Real-Time Multimedia

-   **Audio Calling**: A TCP-based server and client system for routing audio data between registered users.

-   **Video Streaming**: A relay server that handles image frame transmission using `struct` for precise data sizing and synchronization.

### 2\. Messaging & File Transfer

-   **Assessment System**: A UDP-based server supporting user registration, "PING/PONG" connectivity checks, and formatted message routing.

-   **Integrated Mail Service**: Advanced implementations for sending text messages and file attachments simultaneously over a network.

-   **File Relaying**: Servers capable of handling file headers (name and size) to ensure complete data transfer between clients.

### 3\. Network Utilities

-   **RTT Testing**: Tools to measure Round Trip Time (RTT) between a client and a UDP server.

-   **Time Services**: A simple UDP server that provides the current date and time upon request.

-   **Basic Echo**: Standard echo servers and clients for testing basic socket connectivity.

File Structure
--------------

-   `Assessment/`: Multi-functional UDP messaging and file routing.

-   `Audio call/`: TCP-based audio communication scripts.

-   `video call/`: Video relay server and client implementation.

-   `file+msg in mail/`: SMTP-style communication for combined data types.

-   `RTT_server.py` / `RTT_client.py`: Network latency testing.

-   `UDP_Server.py` / `UDP_Client.py`: Basic datagram communication and time retrieval.

Prerequisites
-------------

-   **Python 3.x**

-   **Standard Libraries**: `socket`, `threading`, `struct`, `datetime`.

-   **Optional Dependencies**: `cv2` (OpenCV) and `pyaudio` may be required for certain multimedia client scripts to capture hardware input.

Getting Started
---------------

1.  **Start the Server**: Run the server script for the desired module (e.g., the Video Server):

    Bash

    ```
    python "video call/server.py"

    ```

    *The server will typically bind to `127.0.0.1` and a specific port (e.g., 7777, 8080, or 12345).*

2.  **Connect the Client**: Open a new terminal and run the corresponding client script:

    Bash

    ```
    python "video call/client.py"

    ```

Protocol Details
----------------

-   **UDP**: Used for RTT testing and the Assessment module for low-overhead communication.

-   **TCP**: Used for audio, video, and mail services to ensure reliable, ordered data delivery.
