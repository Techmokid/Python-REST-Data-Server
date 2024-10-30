import subprocess, os, sys
def pipInstall(package):
    with open(os.devnull, 'w') as fnull:
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', package],
                                stdout=fnull, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"Error installing package {package}: {result.stderr}")

try:
    import requests
except:
    pipInstall("requests")

try:
    import colorama
except:
    pipInstall("colorama")

import requests
import hashlib
import time
import socket
import json
import struct
from colorama import Fore, Style, init

SERVER_ADDRESS = "http://[2406:2d40:2031:8100::1001]:8080"
#SERVER_ADDRESS = "http://localhost:8080"
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
        print(f"Found multicast signal: {SERVER_ADDRESS}")
    except socket.timeout:
        print("No multicast response received. Falling back on default localhost\n")
    except OSError as e:
        print(f"Socket error: {e}")

def generate_hash(params, key):
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
    calculated_hash = generate_hash(params, hash_key)
    data = {
        'id': id,
        'key': key,
        'val': val,
        'timestamp': timestamp,
        'hash': calculated_hash
    }
    
    response = requests.post(f"{SERVER_ADDRESS}/editData", data=data)
    #print("Edit Data Response:", response.status_code, response.text)
    return response

def get_data(id, timestamp=None, hash_key=None):
    if id is None:
        response = requests.get(f"{SERVER_ADDRESS}/getData")
    else:
        if timestamp is None or hash_key is None:
            response = requests.get(f"{SERVER_ADDRESS}/getData?id={id}")
        else:
            params = f"id={id}&timestamp={timestamp}"
            provided_hash = generate_hash(params, hash_key)
            response = requests.get(f"{SERVER_ADDRESS}/getData?{params}&hash={provided_hash}")
    
    #print("Get Data Response:", response.status_code, response.text)
    return response




# Annoyingly, windows requires a "color" call before it will display ANSI color codes.
# Excluding this nukes windows ability for color. Windows specific issue, linux does not suffer from this stupidity
# I hate windows so much sometimes...
import os
os.system('color')

def print_result(test, result, details=""):
    origColor = Fore.WHITE
    resultCol = Fore.GREEN if result else Fore.RED
    testCol = Fore.GREEN if test else Fore.RED
    print(f"[RAW ATTEMPT OUTPUT: {resultCol}{'SUCCESS' if result else 'FAILURE'}{origColor}] [TEST RESULTS: {testCol}{'PASS' if test else 'FAIL'}{origColor}] {details}{Style.RESET_ALL}")
    
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
    if edit_data(id, "exampleKey", "exampleValue", timestamp, hash_key).status_code == 200:
        print_result(True, True, "Edit data")
    else:
        print_result(False, False, "Edit data")
    
    # Attempt to retrieve the data
    if get_data(id).status_code == 200:
        print_result(True, True, "Get data")
    else:
        print_result(False, False, "Get data")

    if edit_data(id, "RestrictAccess", "True", timestamp, hash_key).status_code == 200:
        print_result(True, True, "Set data to restricted access")
    else:
        print_result(False, False, "Set data to restricted access")

    params = f"id={id}&key=FinalClientTest&val=True&timestamp={timestamp}"
    hashVal = generate_hash(params, hash_key)
    response = requests.get(f"{SERVER_ADDRESS}/getData?{params}&hash={hashVal}")
    if response.status_code == 200:
        print_result(True, True, "Get restricted data: " + str(response.text.strip()))
    else:
        print_result(False, False, "Get restricted data: " + str(response.text.strip()))




        
    
    # Simulate error cases
    print("\nSimulating Error Cases:")
    params_dict = {
        'id': id,
        'key': 'exampleKey'
    }
    response = requests.post(f"{SERVER_ADDRESS}/editData",data=params_dict)
    if response.status_code == 200:
        print_result(False, True, "Edit data: Missing Parameters: " + str(response.text.strip()))
    else:
        print_result(True, False, "Edit data: Missing Parameters: " + str(response.text.strip()))
    
    # Non-existent ID in editData
    response = edit_data(99999,'exampleKey','exampleValue',timestamp,'wronghash')
    if response.status_code == 200:
        print_result(False, True, "Edit data: Non-existent ID: " + str(response.text.strip()))
    else:
        print_result(True, False, "Edit data: Non-existent ID: " + str(response.text.strip()))
    
    # Incorrect hash in editData
    response = edit_data(id,'exampleKey','exampleValue',timestamp,'wronghash')
    if response.status_code == 200:
        print_result(False, True, "Edit data: Incorrect hash: " + str(response.text.strip()))
    else:
        print_result(True, False, "Edit data: Incorrect hash: " + str(response.text.strip()))
    
    # Outdated timestamp in editData
    outdated_timestamp = timestamp - 100
    response = edit_data(id,'exampleKey','exampleValue',outdated_timestamp,hash_key)
    if response.status_code == 200:
        print_result(False, True, "Edit data: Outdated timestamp: " + str(response.text.strip()))
    else:
        print_result(True, False, "Edit data: Outdated timestamp: " + str(response.text.strip()))
    
    # Restricted data access without proper parameters
    timestamp = get_timestamp()
    if get_data(id,timestamp).status_code == 200:
        print_result(False, True, "Get data: Accessing restricted data without proper access parameters: " + str(response.text.strip()))
    else:
        print_result(True, False, "Get data: Accessing restricted data without proper access parameters: " + str(response.text.strip()))

    # Attempt to set restricted variable name
    response = edit_data(id,'ClientLatestDataUpdate','17',timestamp,hash_key)
    if response.status_code == 200:
        print_result(False, True, "Edit data: Setting forbidden / restricted variable name: " + str(response.text.strip()))
    else:
        print_result(True, False, "Edit data: Setting forbidden / restricted variable name: " + str(response.text.strip()))






    # Finally finish with functioning response
    print("\nFinal restricted data case:")
    response = edit_data(id,'FinalClientTest','True',timestamp, hash_key)
    if response.status_code == 200:
        print_result(True, True, "Edit data: Correctly formatted restricted value change: " + str(response.text.strip()))
    else:
        print_result(False, False, "Edit data: Correctly formatted restricted value change: " + str(response.text.strip()))


print("Discovering...")
#discover_server()
test_api()
