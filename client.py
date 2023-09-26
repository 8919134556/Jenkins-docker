import socket
import multiprocessing
import concurrent.futures 
import time

def make_request():
    i=0
    start = time.time()
    # Create a TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 5555))

    # Send a request to the server
    latitude = 19.683970
    longitude = 78.751274      
        
    data = "Client_{}, Latitude={}, Longitude={}".format(i+1, latitude, longitude)
    hex_data = data.encode().hex()

    print(hex_data)
    # client_socket.sendall(b"hex_data.encode('utf-8')")
    client_socket.sendall(hex_data.encode('utf-8'))


    # Receive and process the response from the server
    response = client_socket.recv(1024)
    # Process the response or perform any necessary operations
    print(f"Received response: {response.decode()}")

    client_socket.close()
    finish = time.time()
    response_time = finish - start

    return response_time

def start_client():
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # Submit tasks to the thread pool
        futures = [executor.submit(make_request) for i in range(5000)]

        # Wait for the tasks to complete and retrieve the results
        results = [future.result() for future in concurrent.futures.as_completed(futures)]

        finish = time.time()
        # Print the results
        print(f"Results: {len(results)}")
        #print("result", results)
        successes = [i for i in results if i > 0]
        errors = [i for i in results if i <= 0]
        overall_response_time = sum(successes)
        if successes:
            avg_response_time = overall_response_time / len(successes) * 1000  # inms.
        else:
            avg_response_time = 0
        time_spent = finish - start
        rps = 5000 / time_spent

        msg = (
            'Errors: %s, Successes: %s\n'
            'Average Response Time: %s ms\n'
            'Requests per second (avg.): %s req/s\n'
            'Time spent: %s s'
        )
        msg = msg % (
            len(errors),
            len(successes),
            avg_response_time,
            rps,
            time_spent
        )
        print(msg)
   


if __name__ == "__main__":
    # Create multiple processes to handle the client
    start = time.time()
    num_processes = 1
    processes = []

    for _ in range(num_processes):
        process = multiprocessing.Process(target=start_client)
        process.daemon = True
        processes.append(process)
        process.start()

    for process in processes:
        process.join()
    finish = time.time()
    time_spent = finish - start
    msg = (
        'Total Time spent: %s s'
    )
    msg = msg % (
        time_spent
    )
    print(msg)

