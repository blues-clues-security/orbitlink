import socket
import struct
import time
import argparse
import random

# Note the arguements are position sensitive
parser = argparse.ArgumentParser(description='Send a SOSI or TTC data packet with a custom header and payload')
parser.add_argument('src', metavar='SOURCE', type=str, help='the source IP address or hostname')
parser.add_argument('dest', metavar='DESTINATION', type=str, help='the destination IP address or hostname')
parser.add_argument('port', metavar='PORT', type=str, help='the destination port number')
parser.add_argument('payload', metavar='PAYLOAD', type=str, help='Choose SOSI or TTC (case sensitive)')

# Sample execution line: python ol_control_send.py 192.168.0.47 192.168.0.47 12345 SOSI

# Define the packet header format
HEADER_FORMAT = '!4s4sBBHI'

sample_SOSI = [
    # Note for all satellites below these names and coordinates are made up
    # Sample Satellites: US
    'US-GOES-1, 1 12345U 21092A 21291.32000000 .00000000 00000-0 00000-0 0 0013, 2 12345 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7890',
    'US-GEO-1, 1 23456U 21092B 21291.32000000 .00000000 00000-0 00000-0 0 0014, 2 23456 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7891',
    'US-STAR, 1 34567U 21092C 21291.32000000 .00000000 00000-0 00000-0 0 0015, 2 34567 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7892',
    'US-GEOEYE, 1 45678U 21092D 21291.32000000 .00000000 00000-0 00000-0 0 0016, 2 45678 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7893',
    'US-COMSAT, 1 56789U 21092E 21291.32000000 .00000000 00000-0 00000-0 0 0017,2 56789 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7894',
    'US-EAGLE, 1 67890U 21092F 21291.32000000 .00000000 00000-0 00000-0 0 0018,2 67890 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7895',
    'US-VISION, 1 78901U 21092G 21291.32000000 .00000000 00000-0 00000-0 0 0019, 2 78901 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7896',
    # Sample Satellites: RU
    'RU-Gorizont-1, 1 11111U 21092A 21291.32000000 .00000000 00000-0 00000-0 0 0013, 2 11111 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7890',
    'RU-Blagopoluchie-1, 1 22222U 21092B 21291.32000000 .00000000 00000-0 00000-0 0 0014, 2 22222 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7891',
    'RU-Mir-1, 1 33333U 21092C 21291.32000000 .00000000 00000-0 00000-0 0 0015, 2 33333 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7892',
    'RU-Raduga-1, 1 44444U 21092D 21291.32000000 .00000000 00000-0 00000-0 0 0016, 2 44444 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7893',
    'RU-Ekran-1, 1 55555U 21092E 21291.32000000 .00000000 00000-0 00000-0 0 0017, 2 55555 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7894',
    'RU-Express-1, 1 66666U 21092F 21291.32000000 .00000000 00000-0 00000-0 0 0018, 2 66666 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7895',
    'RU-Fregat-1, 1 77777U 21092G 21291.32000000 .00000000 00000-0 00000-0 0 0019, 2 77777 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7896',
    # Sample Satellites: CN
    'CN-Fengyun-1, 1 11111U 21092A 21291.32000000 .00000000 00000-0 00000-0 0 0013, 2 11111 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7890',
    'CN-Tianlian-1, 1 33333U 21092C 21291.32000000 .00000000 00000-0 00000-0 0 0015, 2 33333 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7892',
    'CN-Zhongxing-1, 1 44444U 21092D 21291.32000000 .00000000 00000-0 00000-0 0 0016, 2 44444 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7893',
    'CN-Qianlong-1, 1 55555U 21092E 21291.32000000 .00000000 00000-0 00000-0 0 0017, 2 55555 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7894',
    'CN-Hongyan-1, 1 66666U 21092F 21291.32000000 .00000000 00000-0 00000-0 0 0018, 2 66666 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7895',
    'CN-Beidou-1, 1 77777U 21092G 21291.32000000 .00000000 00000-0 00000-0 0 0019, 2 77777 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7896',
    'CN-Tiantong-1, 1 88888U 21092H 21291.32000000 .00000000 00000-0 00000-0 0 0020, 2 88888 0.0172 184.3376 0003000 97.8654 262.2727 1.00271111 7897'
]
sample_TTC = [
    # Sample Payload 1: Telemetry Data
    "2022-10-25 12:34:56, health:OK, temp:35C, voltage:12.3V, current:2.5A",
    # Sample Payload 2: Tracking Data
    "2022-10-25 12:34:56, lat:10.12345, long:-78.98765, alt:35800km, velocity:2.5km/s",
    # Sample Payload 3: Command Signals
    "2022-10-25 12:34:56, cmd:adjust_attitude, pitch:15deg, roll:5deg, yaw:10deg",
    # Sample Payload 4: Software Updates
    "2022-10-25 12:34:56, version:3.2.1, release_date:2022-10-20",
    # Sample Payload 5: Payload Data
    "2022-10-25 12:34:56, payload_type:camera, resolution:1080p, frame_rate:30fps",
    # Sample Payload 6: Error Correction Codes
    "2022-10-25 12:34:56, error_count:10, error_type:parity",
    # Sample Payload 7: Security Measures
    "2022-10-25 12:34:56, encryption:ON, authentication:ON, access_level:ADMIN"
]
try:
    args = parser.parse_args()
except Exception as e:
    print('Error with {}'.format(e))

# Define the packet header fields
source_address = args.src
destination_address = args.dest # TestWinxp: 192.168.138.234
protocol_id = random.randint(0,255)  # UDP protocol ID
sequence_number = int(args.port)
timestamp = int(time.time())  # Current Unix timestamp

# Create payload
try:
    args.payload
except Exception as e:
    print('Error or no payload set\n{}'.format(e))

if args.payload == 'SOSI':
    payload = sample_SOSI[random.randint(0,len(sample_SOSI)-1)].encode()
elif args.payload == 'TTC':
    payload = sample_TTC[random.randint(0,len(sample_TTC)-1)].encode()
else:
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