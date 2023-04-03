# Archived since compatibility issues with WinXP and Python 3.4
import socket
import struct
import sys
import select
import time

# Define the packet header format
HEADER_FORMAT = '!4s4sBBHI'

# Create a socket and bind to a port to listen for incoming packets
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('0.0.0.0', 12345))  # Listen on all interfaces on port 12345

packet_counter = 0
flush_interval = 1

try:
    with open('ol_data_log.txt', 'ab') as f:  # Open the file in binary append mode
        while True:
            # Wait for incoming packets with a timeout of 1 second
            ready, _, _ = select.select([s], [], [], 1.0)

            if ready:
                packet_counter += 1

                # Receive a packet
                packet, address = s.recvfrom(1024)

                # Unpack the header fields from the packet
                source_address, destination_address, protocol_id, payload_length, sequence_number, timestamp = struct.unpack(HEADER_FORMAT, packet[:16])

                # Extract the payload data from the packet
                payload = packet[12:]

                # Print the packet information and payload data
                print(f'Received packet from {address[0]}:{address[1]}')
                print(f'Source Address: {socket.inet_ntoa(source_address)}')
                print(f'Destination Address: {socket.inet_ntoa(destination_address)}')
                print(f'Payload Length: {payload_length}')
                print(f'Sequence Number: {sequence_number}')
                timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
                print(f'Timestamp: {timestamp_str}')
                print(f'Payload Data: {payload}')

                # Write the packet information and payload data to the file
                f.write(f'Received packet from {address[0]}:{address[1]}\n'.encode())
                f.write(f'Source Address: {socket.inet_ntoa(source_address)}\n'.encode())
                f.write(f'Destination Address: {socket.inet_ntoa(destination_address)}\n'.encode())
                f.write(f'Payload Length: {payload_length}\n'.encode())
                f.write(f'Sequence Number: {sequence_number}\n'.encode())
                f.write(f'Timestamp: {timestamp_str}\n'.encode())
                f.write(f'Payload Data: {payload}\n\n'.encode())

                if packet_counter % flush_interval == 0:
                    f.flush()
                    print('[*] Data written to file.')

except KeyboardInterrupt:
    print('[!] Keyboard interrupt received\n[*] Closing the program...')
    s.close()
    sys.exit(0)