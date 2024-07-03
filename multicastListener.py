import socket
import struct
import json
import os

MULTICAST_GROUP = '224.0.0.1'
MULTICAST_PORT = 5007

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.254.254.254', 1))  # Connect to an address to determine the local IP address
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'  # Default to localhost if unable to determine
    finally:
        s.close()
    return ip

def multicast_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((get_local_ip(), MULTICAST_PORT))

    # Get the local IP address
    local_ip = get_local_ip()
    print(f"Local IP: {local_ip}")

    # Join the multicast group
    mreq = struct.pack("4s4s", socket.inet_aton(MULTICAST_GROUP), socket.inet_aton(local_ip))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"Listening for multicast messages on {MULTICAST_GROUP}:{MULTICAST_PORT}")

    while True:
        data, address = sock.recvfrom(1024)
        if data.decode('utf-8') == 'DISCOVER_SERVER':
            response = json.dumps({'ip': get_local_ip()})
            sock.sendto(response.encode('utf-8'), address)
            print(f"Responded to {address} with IP {get_local_ip()}")

if __name__ == "__main__":
    multicast_listener()
