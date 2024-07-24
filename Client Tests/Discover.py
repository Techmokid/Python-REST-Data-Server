import socket
import json
import struct

MULTICAST_GROUP = '224.0.0.0'
MULTICAST_PORT = 5007
SERVER_ADDRESS = ''

def discover_server():
    global SERVER_ADDRESS
    
    message = 'DISCOVER_SERVER'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(2)
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    
    try:
        sock.sendto(message.encode('utf-8'), (MULTICAST_GROUP, MULTICAST_PORT))
        #print(f"Sent discovery message to {MULTICAST_GROUP}:{MULTICAST_PORT}")

        data, server = sock.recvfrom(1024)
        response = json.loads(data.decode('utf-8'))
        SERVER_ADDRESS = response['ip']
    except socket.timeout:
        print("No multicast response received")
    except OSError as e:
        print(f"Socket error: {e}")

if __name__ == "__main__":
    discover_server()

print("Server IP result: " + SERVER_ADDRESS)
