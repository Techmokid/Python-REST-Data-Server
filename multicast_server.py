if __name__ == "__main__":
    import run
    exit()

import socket
import struct
import json
import threading

MULTICAST_GROUP = '224.0.0.0'
MULTICAST_PORT = 5007
stop_event = threading.Event()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))  # Use Google's DNS to determine the local IP address
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'  # Default to localhost if unable to determine
    finally:
        s.close()
    return ip

def multicast_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MULTICAST_PORT))  # Bind to all interfaces

    local_ip = get_local_ip()
    print(f"Local IP: {local_ip}")

    mreq = struct.pack("4s4s", socket.inet_aton(MULTICAST_GROUP), socket.inet_aton(local_ip))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"Listening for multicast messages on {MULTICAST_GROUP}:{MULTICAST_PORT}")

    while not stop_event.is_set():
        try:
            data, address = sock.recvfrom(1024)
            if data.decode('utf-8') == 'DISCOVER_SERVER':
                response = json.dumps({'ip': local_ip})
                sock.sendto(response.encode('utf-8'), address)
                print(f"Responded to {address} with IP {local_ip}")
        except socket.timeout:
            continue

def start_multicast_server():
    multicast_thread = threading.Thread(target=multicast_server, daemon=True)
    multicast_thread.start()
    return multicast_thread

def stop_multicast_server():
    stop_event.set()
