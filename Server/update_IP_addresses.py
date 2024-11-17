import git, requests, os, json, socket
import datetime

SERVER_ID = 0
def get_public_ipv6():
    try:
        # Use an online service to get the public IPv6 address
        response = requests.get('https://api64.ipify.org?format=json')  # Works for IPv6
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json().get('ip')
    except requests.RequestException as e:
        print(f"Error retrieving public IPv6: {e}")
        return None

def update_ip_in_repo():
    global SERVER_ID
    
    # Path to the GitHub repo and JSON file
    repo_path = os.path.dirname(os.getcwd())
    json_file_path = os.path.join(repo_path, "Server Addresses.json")
    
    # Pull the latest changes from the repository
    repo = git.Repo(repo_path)
    origin = repo.remote(name='origin')
    origin.pull()

    # Update the JSON file
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    
    # Update the JSON based on SERVER_ID
    currentTime = str(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    PORT = 8080
    PUBLIC_IP = get_public_ipv6()
    try:
        server_entry = data["Server Ip Addresses"][SERVER_ID]
        if PUBLIC_IP == server_entry["Public IPv6"]:
            #print(f"[{currentTime}] IPv6 has not changed since last update")
            return PUBLIC_IP,PORT
        
        server_entry["Public IPv6"] = PUBLIC_IP
        server_entry["Port"] = PORT
        server_entry["Last Updated"] = currentTime
    except IndexError:
        newEntry = {
            "Public IPv6" : PUBLIC_IP,
            "Port" : PORT,
            "Last Updated" : currentTime
        }
        data["Server Ip Addresses"].append(newEntry)

    with open(json_file_path, 'w') as file:
        json.dump(data, file, indent=4)

    # Commit and push the changes to the repository
    repo.index.add([json_file_path])
    repo.index.commit("Update server IP and port automatically")
    origin.push()

    print(f"[{currentTime}] Pushed new IP address to Git")
    return PUBLIC_IP,PORT
