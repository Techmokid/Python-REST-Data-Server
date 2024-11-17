# main_script.py
import threading, time, logging, subprocess, os, shutil
from api_server import run as run_api_server
from multicast_server import *
from update_IP_addresses import *

logging.basicConfig(level=logging.INFO)

# Start the API server in a separate thread
api_server_thread = threading.Thread(target=run_api_server, daemon=True)
api_server_thread.start()

# Start the multicast server thread
multicast_thread = threading.Thread(target=multicast_server, daemon=True)
multicast_thread.start()

DATA_DIR = "Stored API Data/"
KEYS_DIR = "Stored API Keys/"
CLIENT_DIR = "Client FTP/"
LOGS_DIR = "Logs/"
def run_server_checks():
    process = subprocess.Popen(
        ["python", "server_check.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    all_passed = True

    while True:
        line = process.stdout.readline()
        if not line:
            break
        print(line, end='')  # Print the line as it comes in
        if "RAW ATTEMPT OUTPUT: " in line and "PASS" not in line:
            all_passed = False
            process.kill()  # Terminate the subprocess
            break
        if "Get new ID:" in line:
            id = line.split(": ")[3].split(" ")[0]
            print("\n\n")
            print("REMOVING ID: " + id)
            os.remove(DATA_DIR + f"KEYVAL{id}.json")
            os.remove(DATA_DIR + f"ACCESS_{id}.txt")
            os.remove(KEYS_DIR + f"{id}.key")
            shutil.rmtree(CLIENT_DIR + f"Client_{id}/")
            print("\n\n")

    process.stdout.close()
    process.wait()

    if all_passed:
        print("All tests passed.")
    else:
        print("Some tests failed. Exiting.")
        exit()

#run_server_checks()

# Monitor the API server and keep the main thread alive
try:
    while True:
        ip,port = update_ip_in_repo()
        print(f"\nStarting server at http://[{ip}]:{port}\n")
        time.sleep(60)  # Keep the main thread alive
except KeyboardInterrupt:
    logging.info("Server shutting down...")
    #stop_multicast_server()  # Stop multicast thread
    api_server_thread.stop()
    multicast_thread.stop()
    logging.info("Server Offline")
