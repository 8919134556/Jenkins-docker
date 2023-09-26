# run_tcp_clients.py
import subprocess

# Define the command to run the TCP client script
command = ["python", "client.py"]

# Create a list to store subprocess objects
processes = []

# Spawn subprocesses
for _ in range(2):
    process = subprocess.Popen(command)
    processes.append(process)

# Wait for all subprocesses to complete
for process in processes:
    process.wait()

print("All subprocesses have finished.")
