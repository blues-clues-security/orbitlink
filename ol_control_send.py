import socket
import struct
import time

# Define the packet header format
HEADER_FORMAT = '!4s4sBBHI'

# Define the packet header fields
source_address = '192.168.0.47'
destination_address = '192.168.0.47'
protocol_id = 17  # UDP protocol ID
sequence_number = 12346
timestamp = int(time.time())  # Current Unix timestamp
payload = b'This is a test payload'
payload_length = len(payload)

# Create a socket and bind to the source address
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((source_address, 0))  # Bind to a random free port

# Pack the header fields into a binary string
header = struct.pack(HEADER_FORMAT, socket.inet_aton(source_address), socket.inet_aton(destination_address), protocol_id, payload_length, sequence_number, timestamp)

# Send the packet with the header and payload
s.sendto(header + payload, (destination_address, 12345))  # Use a random destination port

# Close the socket
s.close()