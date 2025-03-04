import json
import socket

def client(server_process_id: int, client_process_id: int, filename: str, window_size: int, buffer_size: int):
    """Client function to send a file to the server using the Go-Back-N Protocol"""
    # Create and start the client
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_addr: tuple = ("127.0.0.1", 9000 + int(client_process_id))
    client_socket.bind(client_addr)

    server_addr: tuple = ("127.0.0.1", 10000 + int(server_process_id))

    bytes_sent: int = 0
    bytes_received: int = 0
    # Send hello to server
    bytes_sent += client_socket.sendto(b"hello", server_addr)

    # Receive the amount of packets
    message, address = client_socket.recvfrom(buffer_size)
    bytes_received += len(message)
    num_packets: int = int(message.decode())

    # Receive the file
    window_start: int = 0
    window_end: int = window_size - 1
    received_packets: dict[int,bytes] = {}
    packets_received: int = 0
    retransmissions_received: int = 0
    ack_num: int = 0
    client_socket.settimeout(0.1)
    # While not all packets received
    while ack_num < num_packets - 1:
        for _ in range(window_size):
            try:
                message, address = client_socket.recvfrom(buffer_size)
                bytes_received += len(message)
                if message == b"eof":
                    break
            except socket.timeout:
                # Send ack if no new message
                continue
            if address == server_addr:
                # Packet received
                seq_num, data = message.decode().split(" ", 1)
                seq_num = int(seq_num)
                data = bytes(data, "utf-8")
                received_packets[seq_num] = data
                print(f"Received packet {seq_num} from {address}")
                ack_num = len(received_packets) - 1
                packets_received += 1
                window_start += 1
        # Send acks
        ack_message = str(len(received_packets)).encode("utf-8")
        bytes_sent += client_socket.sendto(ack_message, server_addr)
        print(f"Sent ack {ack_num} to {server_addr}")
        if ack_num == len(received_packets) - 1:
            window_start = window_end + 1
            window_end = window_start + window_size - 1
            if window_end > num_packets:
                window_end = num_packets - 1
        else:
            retransmissions_received += 1

    # Write the file
    with open(f"received_data/client_{client_process_id}_{filename}", "wb") as file:
        for i in range(len(received_packets) - 1):
            file.write(received_packets[i])

    # Close the socket
    client_socket.close()

    # Sent stats to stats json
    stats = {
        "type": "Client",
        "process": client_process_id,
        "packets_received": packets_received,
        "bytes_sent": bytes_sent,
        "bytes_received": bytes_received,
        "retransmissions_received": retransmissions_received,
    }
    with open("stats.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    data["processes"].append(stats)
    with open("stats.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
