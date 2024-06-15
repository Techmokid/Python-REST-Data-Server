from flask import Flask, request, jsonify, render_template_string
import os
import json
import hashlib
import secrets
import string

app = Flask(__name__)

DATA_DIR = "Stored API Data/"
KEYS_DIR = "Stored API Keys/"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(KEYS_DIR):
    os.makedirs(KEYS_DIR)


def verify_hash(id, key, val, timestamp, provided_hash):
    # You need to implement your hash verification logic here
    # For example, concatenate id, key, val, timestamp and hash it, then compare with provided_hash
    return True

@app.route('/')
def user_interface():
    return render_template_string("<h1>This website is an API endpoint</h1>"), 404

@app.route('/newID', methods=['GET'])
def new_id():
    # Generate a brand new hash key
    key_length = 32
    hash_key = ''.join(secrets.choice('abcdef' + string.digits) for _ in range(key_length))
    
    # Generate the ID by scanning all files and finding the first non-created id
    id = 0
    while True:
        filename = os.path.join(DATA_DIR, f"KEYVAL{id}.json")
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                json.dump({}, f)  # Initialize with an empty dictionary
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

    # Verify the hash
    if not verify_hash(id, key, val, timestamp, provided_hash):
        return jsonify({'message': 'Hash verification failed'}), 403

    # Check if the ID file exists
    data_file = os.path.join(DATA_DIR, f"KEYVAL{id}.json")
    if not os.path.exists(data_file):
        return jsonify({'message': f'ID {id} does not exist in the system yet'}), 404

    # Load existing data
    with open(data_file, 'r') as f:
        data = json.load(f)

    # Update data with new key-value pair
    data[key] = val

    # Save data to file
    with open(data_file, 'w') as f:
        json.dump(data, f)

    return jsonify({'message': 'Data updated successfully'}), 200


























if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80)
