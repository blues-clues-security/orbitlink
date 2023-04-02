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

# Set the timeout for the socket
s.settimeout(5.0)  # 5.0 seconds

try:
    with open('ol_data_log.txt', 'ab') as f:  # Open the file in binary append mode
        while True:
            try:
                # Receive a packet
                packet, address = s.recvfrom(1024)
                packet_counter += 1

                # Unpack the header fields from the packet
                source_address, destination_address, protocol_id, payload_length, sequence_number, timestamp = struct.unpack(HEADER_FORMAT, packet[:16])

                # Extract the payload data from the packet
                payload = packet[16:]

                # Print the packet information and payload data
                print('Received packet from {}:{}'.format(address[0], address[1]))
                print('Source Address: {}'.format(socket.inet_ntoa(source_address)))
                print('Destination Address: {}'.format(socket.inet_ntoa(destination_address)))
                print('Payload Length: {}'.format(payload_length))
                print('Sequence Number: {}'.format(sequence_number))
                timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
                print('Timestamp: {}'.format(timestamp_str))
                print('Payload Data: {}'.format(payload))

                # Write the packet information and payload data to the file
                f.write('Received packet from {}:{}\n'.format(address[0], address[1]).encode())
                f.write('Source Address: {}\n'.format(socket.inet_ntoa(source_address)).encode())
                f.write('Destination Address: {}\n'.format(socket.inet_ntoa(destination_address)).encode())
                f.write('Payload Length: {}\n'.format(payload_length).encode())
                f.write('Sequence Number: {}\n'.format(sequence_number).encode())
                f.write('Timestamp: {}\n'.format(timestamp_str).encode())
                f.write('Payload Data: {}\n\n'.format(payload).encode())

                if packet_counter % flush_interval == 0:
                    f.flush()
                    print('[*] Data written to file.')

            except socket.timeout:
                # No packet received within the timeout period
                timestamp = time.time()
                timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
                f.write('No data received, Timestamp: {}\n'.format(timestamp_str).encode())
                f.write('\n')
                continue
                
    
except KeyboardInterrupt:
    print('[!] Keyboard interrupt received\n[*] Closing the program...')
    s.close()
    sys.exit(0)