import os,shutil

paths = ["Stored API Data/","Stored API Keys/","Client FTP/","Logs/"]
for i in paths:
    if os.path.exists(i):
        try:
            shutil.rmtree(i)
        except:
            print(f"Error deleting directory: {i}")

input("Task complete")
