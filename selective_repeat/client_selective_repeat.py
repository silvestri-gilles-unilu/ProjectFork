import socket


def client(server_process_id: int, client_process_id: int, filename: str, window_size: int, chunk_size: int):
    """Client function to send a file to the server using the Selective-Repeat Protocol"""
    # Create and start the client
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_addr: tuple = ("127.0.0.1", 9000 + int(client_process_id))
    client_socket.bind(client_addr)

    server_addr: tuple = ("127.0.0.1", 10000 + int(server_process_id))

    # Send hello to server
    client_socket.sendto(b"hello", server_addr)

    # Receive the amount of packets
    message, address = client_socket.recvfrom(1024)
    num_packets: int = int(message.decode())

    # Receive the file
    received_packets: dict[int, bytes] = {}
    client_socket.settimeout(0.1)
    # While client is connected to server
    while True:
        try:
            message, address = client_socket.recvfrom(chunk_size)
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
            if seq_num not in received_packets:
                received_packets[seq_num] = data
                print(f"Received packet {seq_num} from {address}")
                # Send ack
                client_socket.sendto(bytes(str(seq_num), "utf-8"), server_addr)
                print(f"Sent ack {seq_num} to {server_addr}")
    # Write the file
    with open(f"received_data/client_{client_process_id}_{filename}", "wb") as file:
        for i in range(len(received_packets)):
            file.write(received_packets[i])

    # Close the socket
    client_socket.close()
