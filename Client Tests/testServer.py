import requests
import hashlib
import time
import socket
import json
import struct
from colorama import Fore, Style, init

SERVER_ADDRESS = "http://127.0.0.1"  # Replace with your server's IP if it's hosted remotely
MULTICAST_GROUP = '224.0.0.0'
MULTICAST_PORT = 5007

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
        SERVER_ADDRESS = 'http://' + response['ip']
    except socket.timeout:
        print("No multicast response received")
    except OSError as e:
        print(f"Socket error: {e}")

def generate_hash(id, params, key):
    data_to_hash = key + params
    hash_object = hashlib.sha256(data_to_hash.encode())
    return hash_object.hexdigest()

def create_new_id():
    response = requests.get(f"{SERVER_ADDRESS}/newID")
    if response.status_code == 200:
        return response.json()
    else:
        print("Error creating new ID:", response.text)
        return None

def get_timestamp():
    response = requests.get(f"{SERVER_ADDRESS}/getTimestamp")
    if response.status_code == 200:
        return int(response.text)
    else:
        print("Error getting timestamp:", response.text)
        return None

def edit_data(id, key, val, timestamp, hash_key):
    params = f"id={id}&key={key}&val={val}&timestamp={timestamp}"
    provided_hash = generate_hash(id, params, hash_key)
    response = requests.get(f"{SERVER_ADDRESS}/editData?{params}&hash={provided_hash}")
    #print("Edit Data Response:", response.status_code, response.text)
    return response.status_code

def get_data(id, timestamp=None, hash_key=None):
    if id is None:
        response = requests.get(f"{SERVER_ADDRESS}/getData")
    else:
        if timestamp is None or hash_key is None:
            response = requests.get(f"{SERVER_ADDRESS}/getData?id={id}")
        else:
            params = f"id={id}&timestamp={timestamp}"
            provided_hash = generate_hash(id, params, hash_key)
            response = requests.get(f"{SERVER_ADDRESS}/getData?{params}&hash={provided_hash}")
    
    #print("Get Data Response:", response.status_code, response.text)
    return response.status_code




# Annoyingly, windows requires a "color" call before it will display ANSI color codes.
# Excluding this nukes windows ability for color. Windows specific issue, linux does not suffer from this stupidness
import os
os.system('color')

def print_result(test, result, details=""):
    origColor = Fore.WHITE
    resultCol = Fore.GREEN if result else Fore.RED
    testCol = Fore.GREEN if test else Fore.RED
    print(f"[RESULT: {resultCol}{'SUCCESS' if result else 'FAILURE'}{origColor}] [TEST: {testCol}{'SUCCESS' if test else 'FAILURE'}{origColor}] {details}{Style.RESET_ALL}")
    
def test_api():
    # Create a new ID
    print("Starting tests")
    id_info = create_new_id()
    if not id_info:
        print_result(False, False, "Get new ID")
        return

    id = id_info['id']
    hash_key = id_info['hash_key']
    print_result(True, True, f"Get new ID: {id} with hashkey {hash_key}")
    
    # Get the current timestamp
    timestamp = get_timestamp()
    if not timestamp:
        print_result(False, False, "Get server timestamp")
        return
    print_result(True,True,  f"Get server timestamp: {timestamp}")
    
    # Edit data for the new ID
    if edit_data(id, "exampleKey", "exampleValue", timestamp, hash_key) == 200:
        print_result(True, True, "Edit data")
    else:
        print_result(False, False, "Edit data")
    
    # Attempt to retrieve the data
    if get_data(id) == 200:
        print_result(True, True, "Get data")
    else:
        print_result(False, False, "Get data")

    if edit_data(id, "DataAccessLevel", "Restricted", timestamp, hash_key) == 200:
        print_result(True, True, "Set data to restricted access")
    else:
        print_result(False, False, "Set data to restricted access")
    
    # Simulate error cases
    print("\nSimulating Error Cases:")
    response = requests.get(f"{SERVER_ADDRESS}/editData?id={id}&key=exampleKey")
    if response.status_code == 200:
        print_result(False, True, "Edit data: Missing Parameters")
    else:
        print_result(True, False, "Edit data: Missing Parameters")
    
    # Non-existent ID in editData
    response = requests.get(f"{SERVER_ADDRESS}/editData?id=99999&key=exampleKey&val=exampleValue&timestamp={timestamp}&hash=wronghash")
    if response.status_code == 200:
        print_result(False, True, "Edit data: Non-existent ID")
    else:
        print_result(True, False, "Edit data: Non-existent ID")
    
    # Incorrect hash in editData
    response = requests.get(f"{SERVER_ADDRESS}/editData?id={id}&key=exampleKey&val=exampleValue&timestamp={timestamp}&hash=wronghash")
    if response.status_code == 200:
        print_result(False, True, "Edit data: Incorrect hash")
    else:
        print_result(True, False, "Edit data: Incorrect hash")
    
    # Outdated timestamp in editData
    outdated_timestamp = timestamp - 100
    response = requests.get(f"{SERVER_ADDRESS}/editData?id={id}&key=exampleKey&val=exampleValue&timestamp={outdated_timestamp}&hash={generate_hash(id, f'id={id}&key=exampleKey&val=exampleValue&timestamp={outdated_timestamp}', hash_key)}")
    if response.status_code == 200:
        print_result(False, True, "Edit data: Outdated timestamp")
    else:
        print_result(True, False, "Edit data: Outdated timestamp")
    
    # Restricted data access without proper parameters
    response = requests.get(f"{SERVER_ADDRESS}/getData?id={id}&timestamp={timestamp-60}")
    if response.status_code == 200:
        print_result(False, True, "Get data: Accessing restricted data without proper access parameters")
    else:
        print_result(True, False, "Get data: Accessing restricted data without proper access parameters")


if __name__ == "__main__":
    discover_server()
    test_api()
