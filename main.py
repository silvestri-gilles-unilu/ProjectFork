# pylint: disable=C0415
import json
import sys
import threading
from tabulate import tabulate


def main():
    """Main function to start server and clients"""
    # Parse the args
    process_id: int = int(sys.argv[1])
    num_processes: int = int(sys.argv[2])
    filename: str = sys.argv[3]
    probability: float = float(sys.argv[4])
    protocol: str = sys.argv[5]
    window_size: int = int(sys.argv[6])

    # Import given protocol
    if protocol == "Go-Back-N":
        from go_back_n import server
        from go_back_n import client
    elif protocol == "Selective-Repeat":
        from selective_repeat import server
        from selective_repeat import client
    else:
        print("Wrong protocol given.(Use: Go-Back-N or Selective-Repeat)")
        return

    # Set chunk_size & buffer_size
    chunk_size: int = 3072
    buffer_size: int = 10240

    # Create and start the server
    server_thread = threading.Thread(target=server, args=(
        process_id, num_processes, filename, probability, window_size, chunk_size))
    server_thread.start()

    # Create and start the clients
    client_threads = []
    for i in range(num_processes):
        client_thread = threading.Thread(target=client, args=(
            process_id, i, filename, window_size, buffer_size))
        client_thread.start()
        client_threads.append(client_thread)

    # Wait for the processes to finish
    server_thread.join()
    for client_thread in client_threads:
        client_thread.join()

    # Print the stats
    with open("stats.json", "r", encoding="utf-8") as file:
        stats = json.load(file)
    processes = stats.get("processes")

    server_stats = []
    clients = []
    for process in processes:
        if process.get("type") == "Server":
            server_stats.append(process.get("type"))
            server_stats.append(process.get("process"))
            server_stats.append(process.get("time"))
            server_stats.append(process.get("packets_sent"))
            server_stats.append(process.get("bytes_sent"))
            server_stats.append(process.get("bytes_received"))
            server_stats.append(process.get("retransmissions_sent"))
        if process.get("type") == "Client":
            client_stats = []
            client_stats.append(process.get("type"))
            client_stats.append(process.get("process"))
            client_stats.append(process.get("packets_received"))
            client_stats.append(process.get("bytes_sent"))
            client_stats.append(process.get("bytes_received"))
            client_stats.append(process.get("retransmissions_received"))
            clients.append(client_stats)
    print()
    print(tabulate([server_stats], headers=["Type", "Process", "Time", "Packets sent",
          "Bytes sent", "Bytes received", "Retransmissions sent"], tablefmt="psql"))
    print()
    print(tabulate(clients, headers=["Type", "Process", "Packets received",
          "Bytes sent", "Bytes received", "Retransmissions received"], tablefmt="psql"))

    # Reset stats file
    reset = {
        "processes": []
    }
    with open("stats.json", "w", encoding="utf-8") as file:
        json.dump(reset, file)


if __name__ == "__main__":
    main()
