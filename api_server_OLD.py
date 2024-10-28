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
LOGS_DIR = "Logs/"

# Set up directories
for dir_path in [DATA_DIR, KEYS_DIR, LOGS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

now = datetime.now()
LOG_FILE = os.path.join(LOGS_DIR, now.strftime("%Y-%m-%d_%H-%M-%S") + ".log")
logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

# Utility function to log events
def writeToLogFile(stringToSave):
    logging.info(stringToSave)
writeToLogFile("Starting up...")

# Define API Routes
def verify_hash(id, paramString, provided_hash):
    try:
        with open(os.path.join(KEYS_DIR, f"{id}.key"), 'r') as f:
            local_key = f.read().strip()
        data_to_hash = local_key + paramString
        calculated_hash = hashlib.sha256(data_to_hash.encode()).hexdigest()
        return calculated_hash == provided_hash
    except FileNotFoundError:
        return False

@app.route('/')
def user_interface():
    return render_template_string("<h1>This website is an API endpoint</h1>"), 404

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
    with open(os.path.join(DATA_DIR, f"KEYVAL{id}.json"), 'w') as f:
        json.dump({"last_communication": int(time.time())}, f)
    with open(os.path.join(KEYS_DIR, f"{id}.key"), 'w') as f:
        f.write(hash_key)
    return jsonify({'id': id, 'hash_key': hash_key}), 200

@app.route('/editData', methods=['GET'])
def edit_data():
    params = {k: request.args.get(k) for k in ['id', 'key', 'val', 'timestamp', 'hash']}
    if any(v is None for v in params.values()):
        return jsonify({'message': 'Missing parameters'}), 403
    data_file = os.path.join(DATA_DIR, f"KEYVAL{params['id']}.json")
    if not os.path.exists(data_file):
        return jsonify({'message': f'ID {params["id"]} does not exist'}), 403
    if abs(int(params['timestamp']) - int(time.time())) > MAX_TIMESTAMP_OFFSET:
        return jsonify({'message': 'Timestamp offset too high'}), 403
    paramHashData = request.query_string.decode('utf-8')[:request.query_string.decode('utf-8').rfind('&')]
    if not verify_hash(params['id'], paramHashData, params['hash']):
        return jsonify({'message': 'Hash verification failed'}), 403
    with open(data_file, 'r+') as f:
        data = json.load(f)
        data[params['key']] = params['val']
        data["ClientLatestDataUpdate"] = int(time.time())
        f.seek(0)
        json.dump(data, f)
        f.truncate()
    return jsonify({'message': 'Data updated successfully'}), 200

@app.route('/getData', methods=['GET'])
def get_data():
    id = request.args.get('id')
    if id:
        return get_individual_data(id)
    else:
        all_data = {f.split('.')[0]: json.load(open(os.path.join(DATA_DIR, f)))
                    for f in os.listdir(DATA_DIR) if f.endswith('.json')}
        return jsonify(all_data), 200

def get_individual_data(id):
    try:
        with open(os.path.join(DATA_DIR, f"KEYVAL{id}.json"), 'r') as f:
            data = json.load(f)
        return jsonify(data), 200
    except FileNotFoundError:
        return jsonify({'message': f'ID {id} not found'}), 403


def run():
    app.run(host='0.0.0.0', port=80)

