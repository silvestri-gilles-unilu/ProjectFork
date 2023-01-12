import random
import socket
import time


def server(process_id: int, num_processes: int, filename: str, probability: float, window_size: int, chunk_size: int):
    """Server function to send the file to the clients using the Selective-Repeat protocol"""
    # Create and start the server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_addr = ("127.0.0.1", 10000 + int(process_id))
    server_socket.bind(server_addr)

    # Wait for all clients to connect
    ready_clients: list[tuple] = []
    while len(ready_clients) < int(num_processes):
        data, address = server_socket.recvfrom(1024)
        print(f"received {len(data)} bytes from {address}")
        if data == b"hello":
            ready_clients.append(address)

    # Prepare the packets
    packets: list[bytes] = []
    with open(filename, "rb") as file:
        while True:
            packet = file.read(chunk_size)
            if packet == b"":
                break
            packets.append(packet)

    start_time = time.time()

    # Send the amount of packets to the clients
    for client in ready_clients:
        server_socket.sendto(bytes(str(len(packets)), "utf-8"), client)
        print(f"Sent amount of packets to {client}")

    # Send the file to all clients
    sent_packets = 0
    packets_sent: dict[tuple, list[bytes]] = {}
    for client in ready_clients:
        packets_sent[client] = []
    seq_num: int = 0
    window_start: int = 0
    window_end = window_size - 1
    datagram_seq_num = window_start
    acked_packets = {client: [] for client in ready_clients}
    last_packet_sent = {client: -1 for client in ready_clients}
    while seq_num < len(packets):
        # Send the window
        for client in ready_clients:
            if seq_num in acked_packets[client]:
                continue
            if probability < random.random():
                # Pack the packet with the seq_num into a message
                message = f"{seq_num} {packets[seq_num]}".encode("utf-8")
                server_socket.sendto(message, client)
                packets_sent[client].append(packet)
                print(f"Sent packet {seq_num}/{len(packets)} to {client}")
                last_packet_sent[client] = seq_num
                sent_packets += 1
            else:
                print(f"Packet {seq_num} lost")
            seq_num += 1
        # Wait for acks and resend packets if necessary
        while True:
            try:
                data, address = server_socket.recvfrom(1024)
                ack_num = int(data.decode())
                if ack_num not in acked_packets[address]:
                    acked_packets[address].append(ack_num)
                for client, last_sent in last_packet_sent.items():
                    if acked_packets[client] and acked_packets[client][-1] is not None and last_sent < acked_packets[client][-1]:
                        window_start = acked_packets[client][-1] + 1
                        window_end = window_start + window_size - 1
                        if window_end > len(packets):
                            window_end = len(packets) - 1
                        last_packet_sent[client] = window_end
                        seq_num = window_start
                if all(acked_packets[client][-1] == len(packets) - 1 for client in ready_clients):
                    break
            except socket.timeout:
                break

    # Close the socket
    server_socket.close()
