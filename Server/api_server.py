if __name__ == "__main__":
    import run
    exit()

# api_server.py
from flask import Flask, request, jsonify, render_template_string
import os, json, hashlib, secrets, string, time, logging
from datetime import datetime

app = Flask(__name__)

# Constants and configurations
MAX_TIMESTAMP_OFFSET = 30
DATA_DIR = "Stored API Data/"
KEYS_DIR = "Stored API Keys/"
FTP_DIR =  "Client FTP/"
LOGS_DIR = "Logs/"

FORBIDDEN_VARS = ["ClientLatestDataUpdate","last_communication"]

# Set up directories
for dir_path in [DATA_DIR, KEYS_DIR, LOGS_DIR, FTP_DIR]:
    os.makedirs(dir_path, exist_ok=True)

now = datetime.now()
LOG_FILE = os.path.join(LOGS_DIR, now.strftime("%Y-%m-%d_%H-%M-%S") + ".log")
logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

# Utility function to log events
def writeToLogFile(stringToSave):
    logging.info(stringToSave)
writeToLogFile("Starting up...")

def run():
    app.run(host='::', port=8080)












# --------------------------------------------------------------------------------
# --------------                                                    --------------
# --------------                                                    --------------
# --------------             Main core Server Functions             --------------
# --------------                                                    --------------
# --------------                                                    --------------
# --------------------------------------------------------------------------------

# Function to verify hash for data integrity
def verify_hash(id, paramString, provided_hash):
    try:
        with open(os.path.join(KEYS_DIR, f"{id}.key"), 'r') as f:
            local_key = f.read().strip()
        data_to_hash = local_key + paramString
        calculated_hash = hashlib.sha256(data_to_hash.encode()).hexdigest()
        return calculated_hash == provided_hash
    except FileNotFoundError:
        return False

# Helper function to log client IP and access time
def log_client_access(id, ip):
    access_file = os.path.join(DATA_DIR, f"ACCESS_{id}.txt")
    with open(access_file, 'w') as f:
        f.write(f"Last IP: {ip}\nLast Access Time: {datetime.now()}\n")

# Define API Routes
@app.route('/')
def user_interface():
    return render_template_string("<h1>This website is andreys API endpoint</h1>"), 404

@app.route('/getTimestamp')
def get_timestamp():
    return str(int(time.time())), 200

@app.route('/newID', methods=['GET'])
def new_id():
    key_length = 32
    hash_key = ''.join(secrets.choice('abcdef' + string.digits) for _ in range(key_length))
    
    id = 0
    while os.path.exists(os.path.join(DATA_DIR, f"KEYVAL{id}.json")):
        id += 1
    
    # Create data file and key for the new client
    with open(os.path.join(DATA_DIR, f"KEYVAL{id}.json"), 'w') as f:
        json.dump({"last_communication": int(time.time())}, f)
    
    with open(os.path.join(KEYS_DIR, f"{id}.key"), 'w') as f:
        f.write(hash_key)
    
    # Create a unique FTP directory for client
    client_ftp_dir = os.path.join(FTP_DIR, f"Client_{id}")
    os.makedirs(client_ftp_dir, exist_ok=True)
    return jsonify({'id': id, 'hash_key': hash_key}), 200

@app.route('/editData', methods=['POST'])
def edit_data():
    params = {k: request.form.get(k) for k in ['id', 'key', 'val', 'timestamp', 'hash']}
    
    if any(v is None for v in params.values()):
        return jsonify({'message': 'Missing parameters'}), 403
    
    if abs(int(params['timestamp']) - int(time.time())) > MAX_TIMESTAMP_OFFSET:
        return jsonify({'message': 'Timestamp offset too high'}), 403
    
    data_file = os.path.join(DATA_DIR, f"KEYVAL{params['id']}.json")
    if not os.path.exists(data_file):
        return jsonify({'message': f'ID {params["id"]} does not exist'}), 403
    
    paramHashData = '&'.join(f"{k}={params[k]}" for k in params if k != 'hash')
    if not verify_hash(params['id'], paramHashData, params['hash']):
        return jsonify({'message': 'Hash verification failed'}), 403

    # Check for forbidden variable names
    if params['key'] in FORBIDDEN_VARS:
        return jsonify({'message': 'This key is forbidden'}), 403

    with open(data_file, 'r+') as f:
        data = json.load(f)
        data[params['key']] = params['val']
        data["ClientLatestDataUpdate"] = int(time.time())
        f.seek(0)
        json.dump(data, f)
        f.truncate()
    
    # Log client IP and access time
    log_client_access(params['id'], request.remote_addr)
    return jsonify({'message': 'Data updated successfully'}), 200

@app.route('/getData', methods=['GET'])
def get_data():
    id = request.args.get('id')
    timestamp = request.args.get('timestamp')
    provided_hash = request.args.get('hash')
    
    if not id:
        return jsonify("{\"Error\":\"No id given\"}"), 400

    # ID was given
    try:
        with open(os.path.join(DATA_DIR, f"KEYVAL{id}.json"), 'r') as f:
            data = json.load(f)

        # If not restricted access, just return the data no problems
        if data.get("RestrictAccess") != "True":
            return jsonify(data), 200
        
        # If restricted access, only allow access if they pass hash tests
        if (timestamp == None) or (provided_hash == None):
            return jsonify({"Error": "Restricted access to client data, missing hash or timestamp"}), 403
        return jsonify(data), 200
    
        paramsHashData = '&'.join(f"{k}={params[k]}" for k in params if k != 'hash')
        if not verify_hash(id,paramsHashData,provided_hash):
            return jsonify({"Error": "Restricted access to client data, invalid hash"}), 403
        
        return jsonify(data), 200
    except FileNotFoundError:
        return jsonify({'message': f'ID {id} not found'}), 400












# --------------------------------------------------------------------------------
# --------------                                                    --------------
# --------------                                                    --------------
# --------------                FTP Server Functions                --------------
# --------------                                                    --------------
# --------------                                                    --------------
# --------------------------------------------------------------------------------
@app.route('/getFileList', methods=['GET'])
def get_file_list():
    id = request.args.get('id')
    
    client_ftp_dir = os.path.join(FTP_DIR, f"Client_{id}")
    if not os.path.exists(client_ftp_dir):
        return jsonify({'message': 'Client FTP directory does not exist'}), 403
    
    files = os.listdir(client_ftp_dir)
    return jsonify({'files': files}), 200






