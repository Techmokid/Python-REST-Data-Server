import socket
import json
import struct

MULTICAST_GROUP = '224.0.0.1'
MULTICAST_PORT = 5007

def discover_server():
    message = 'DISCOVER_SERVER'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(2)
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    sock.sendto(message.encode('utf-8'), (MULTICAST_GROUP, MULTICAST_PORT))

    try:
        data, server = sock.recvfrom(1024)
        response = json.loads(data.decode('utf-8'))
        print(f"Server IP: {response['ip']}")
    except socket.timeout:
        print("No response received")

if __name__ == "__main__":
    discover_server()
