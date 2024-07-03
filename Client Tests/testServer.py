import requests
import hashlib
import time
import socket
import json
import struct

BASE_URL = "http://127.0.0.1"  # Replace with your server's IP if it's hosted remotely

MULTICAST_GROUP = '224.0.0.1'
MULTICAST_PORT = 5007

def generate_hash(id, params, key):
    data_to_hash = key + params
    hash_object = hashlib.sha256(data_to_hash.encode())
    return hash_object.hexdigest()

def create_new_id():
    response = requests.get(f"{BASE_URL}/newID")
    if response.status_code == 200:
        return response.json()
    else:
        print("Error creating new ID:", response.text)
        return None

def get_timestamp():
    response = requests.get(f"{BASE_URL}/getTimestamp")
    if response.status_code == 200:
        return int(response.text)
    else:
        print("Error getting timestamp:", response.text)
        return None

def edit_data(id, key, val, timestamp, hash_key):
    params = f"id={id}&key={key}&val={val}&timestamp={timestamp}"
    provided_hash = generate_hash(id, params, hash_key)
    response = requests.get(f"{BASE_URL}/editData?{params}&hash={provided_hash}")
    print("Edit Data Response:", response.status_code, response.text)

def get_data(id, timestamp=None, hash_key=None):
    if id is None:
        response = requests.get(f"{BASE_URL}/getData")
    else:
        if timestamp is None or hash_key is None:
            response = requests.get(f"{BASE_URL}/getData?id={id}")
        else:
            params = f"id={id}&timestamp={timestamp}"
            provided_hash = generate_hash(id, params, hash_key)
            response = requests.get(f"{BASE_URL}/getData?{params}&hash={provided_hash}")
    
    print("Get Data Response:", response.status_code, response.text)

def discover_server():
    message = 'DISCOVER_SERVER'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(2)
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    try:
        sent = sock.sendto(message.encode('utf-8'), (MULTICAST_GROUP, MULTICAST_PORT))
        while True:
            try:
                data, server = sock.recvfrom(1024)
                print('Received response from server:', json.loads(data.decode('utf-8')))
            except socket.timeout:
                print('Timed out, no more responses')
                break
    finally:
        sock.close()
        
# Testing script
def test_api():
    # Create a new ID
    id_info = create_new_id()
    if not id_info:
        return
    
    id = id_info['id']
    hash_key = id_info['hash_key']
    
    # Get the current timestamp
    timestamp = get_timestamp()
    if not timestamp:
        return
    
    # Edit data for the new ID
    edit_data(id, "exampleKey", "exampleValue", timestamp, hash_key)
    
    # Attempt to retrieve the data
    get_data(id)
    
    # Simulate error cases
    print("\nSimulating Error Cases:\n")
    
    # Missing parameters in editData
    response = requests.get(f"{BASE_URL}/editData?id={id}&key=exampleKey")
    print("Edit Data Missing Params Response:", response.status_code, response.text)
    
    # Non-existent ID in editData
    response = requests.get(f"{BASE_URL}/editData?id=99999&key=exampleKey&val=exampleValue&timestamp={timestamp}&hash=wronghash")
    print("Edit Data Non-existent ID Response:", response.status_code, response.text)
    
    # Incorrect hash in editData
    response = requests.get(f"{BASE_URL}/editData?id={id}&key=exampleKey&val=exampleValue&timestamp={timestamp}&hash=wronghash")
    print("Edit Data Incorrect Hash Response:", response.status_code, response.text)
    
    # Outdated timestamp in editData
    outdated_timestamp = timestamp - 100
    response = requests.get(f"{BASE_URL}/editData?id={id}&key=exampleKey&val=exampleValue&timestamp={outdated_timestamp}&hash={generate_hash(id, f'id={id}&key=exampleKey&val=exampleValue&timestamp={outdated_timestamp}', hash_key)}")
    print("Edit Data Outdated Timestamp Response:", response.status_code, response.text)
    
    # Non-existent ID in getData
    get_data(99999)
    
    # Restricted data access without proper parameters
    response = requests.get(f"{BASE_URL}/getData?id={id}&timestamp={timestamp-60}")
    print("Get Data Restricted Access Response:", response.status_code, response.text)

if __name__ == "__main__":
    discover_server()
    
    test_api()
