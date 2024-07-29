from flask import Flask, request, jsonify, render_template_string
import os, json, hashlib, secrets, string, time, socket, struct, threading

app = Flask(__name__)


# Handle multicast server
MULTICAST_GROUP = '224.0.0.0'
MULTICAST_PORT = 5007

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

    while True:
        data, address = sock.recvfrom(1024)
        if data.decode('utf-8') == 'DISCOVER_SERVER':
            response = json.dumps({'ip': local_ip})
            sock.sendto(response.encode('utf-8'), address)
            print(f"Responded to {address} with IP {local_ip}")

# Start the multicast server in a separate thread
multicast_thread = threading.Thread(target=multicast_server, daemon=True)
multicast_thread.start()

# Handle Main API Server
MAX_TIMESTAMP_OFFSET = 30
DATA_DIR = "Stored API Data/"
KEYS_DIR = "Stored API Keys/"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(KEYS_DIR):
    os.makedirs(KEYS_DIR)

def verify_hash(id, paramString, provided_hash):
    with open(os.path.join(KEYS_DIR,f"{id}.key"),'r') as f:
        local_key = f.read().strip()

    data_to_hash = local_key + paramString
    hash_object = hashlib.sha256(data_to_hash.encode())
    calculated_hash = hash_object.hexdigest()

    return calculated_hash == provided_hash

@app.route('/')
def user_interface():
    return render_template_string("<h1>This website is an API endpoint</h1>"), 404

@app.route('/getTimestamp')
def get_timestamp():
    return str(getTimestamp()),200
def getTimestamp():
    return int(time.time())

@app.route('/newID', methods=['GET'])
def new_id():
    key_length = 32
    hash_key = ''.join(secrets.choice('abcdef' + string.digits) for _ in range(key_length))

    id = 0
    while True:
        filename = os.path.join(DATA_DIR, f"KEYVAL{id}.json")
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                json.dump({"last_communication": getTimestamp()}, f)
            with open(os.path.join(KEYS_DIR, f"{id}.key"), 'w') as f:
                f.write(hash_key)
            break
        id += 1

    return jsonify({'id': id, 'hash_key': hash_key}), 200

@app.route('/editData', methods=['GET'])
def edit_data():
    id = request.args.get('id')
    key = request.args.get('key')
    val = request.args.get('val')
    timestamp = request.args.get('timestamp')
    provided_hash = request.args.get('hash')
    paramHashData = request.query_string.decode('utf-8')[:request.query_string.decode('utf-8').rfind('&')]

    if key == "ClientLatestDataUpdate":
        return jsonify({'message': 'Forbidden variable name due to internal server use'}), 403
    
    if id==None or key==None or val==None or timestamp==None or provided_hash==None:
        return jsonify({'message': f'At least one parameter was missing from the request'}), 403

    data_file = os.path.join(DATA_DIR, f"KEYVAL{id}.json")
    if not os.path.exists(data_file):
        return jsonify({'message': f'ID {id} does not exist in the system yet'}), 403

    if abs(int(timestamp)-getTimestamp()) > MAX_TIMESTAMP_OFFSET:
        return jsonify({'message': f'The timestamp was too far out from the server time'}), 403

    if not verify_hash(id, paramHashData, provided_hash):
        return jsonify({'message': 'Hash verification failed'}), 403

    with open(data_file, 'r') as f:
        data = json.load(f)

    data[key] = val
    data["ClientLatestDataUpdate"] = getTimestamp()  # Update last communication timestamp

    with open(data_file, 'w') as f:
        json.dump(data, f)

    return jsonify({'message': 'Data updated successfully'}), 200

def isRestricted(x):
    x = x.lower()
    if "restrict" in x:
        return True
    if "private" in x:
        return True
    if "lock" in x:
        return True
    return False

@app.route('/getData', methods=['GET'])
def get_data():
    id = request.args.get('id')
    timestamp = request.args.get('timestamp')
    provided_hash = request.args.get('hash')
    paramHashData = request.query_string.decode('utf-8')[:request.query_string.decode('utf-8').rfind('&')]

    if id is None:
        all_data = {}
        for i in os.listdir(DATA_DIR):
            data_file = os.path.join(DATA_DIR, i)
            if data_file.endswith(".json"):
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    if "DataAccessLevel" not in data or not isRestricted(data["DataAccessLevel"]):
                        all_data[i] = data
        return jsonify(all_data), 200
    else:
        data_file = os.path.join(DATA_DIR, f"KEYVAL{id}.json")
        if not os.path.exists(data_file):
            return jsonify({'message': f'ID {id} does not exist in the system yet'}), 403

        with open(data_file, 'r') as f:
            data = json.load(f)
            if "DataAccessLevel" not in data or not isRestricted(data["DataAccessLevel"]):
                return jsonify(data), 200

        if timestamp is None or provided_hash is None:
            return jsonify({'message': f'This ID has set itself to private and at least one parameter was missing from the request'}), 403
        if not verify_hash(id, paramHashData, provided_hash):
            return jsonify({'message': f'This ID has set itself to private and hash verification failed'}), 403
        if abs(int(timestamp)-getTimestamp()) > MAX_TIMESTAMP_OFFSET:
            return jsonify({'message': f'This ID has set itself to private and the timestamp was too far out from the server time'}), 403
        return jsonify(data), 200

    return "Error", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
