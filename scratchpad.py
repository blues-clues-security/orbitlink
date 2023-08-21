import socket, struct, time, os
from datetime import datetime

host = "0.0.0.0"  # Listen on all available network interfaces
port = 6960
max_title_length = 128
header_format = '!4s4sBHHIQ{}s'.format(max_title_length)
header_length = struct.calcsize(header_format)



# Continuously write files received
while True:
    # Create a socket object and bind it to the specified host and port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port)) 

    received_data = {}
    max_sequence_number = None
    image_title = None

    print("Listening for UDP traffic on port {}...".format(port))
    # Continuously listen for incoming UDP traffic
    while True:
        # Receive packet
        packet, addr = sock.recvfrom(65535)
        
        # Unpack header
        header_size = struct.calcsize(header_format)
        header = packet[:header_size]
        src_ip, dest_ip, protocol_id, sequence_number, max_sequence_number, timestamp, payload_length, title = struct.unpack(header_format, header)
        chunk = packet[header_length:header_length+payload_length]
        
        # Store received data
        received_data[sequence_number] = chunk

        if image_title is None:
            image_title = title.rstrip(b'\0').decode()
        
        # Check if all packets received (this is just a simple example, you might want to implement a more robust mechanism)
        if len(received_data) == max_sequence_number + 1:
            break

    # Reconstruct payload
    payload = b''.join([received_data[i] for i in range(max_sequence_number+1)])

    directory = 'images'
    timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d_%H_%M_%S')
    output_file = '{}_{}'.format(timestamp, image_title)
    full_path = os.path.join(directory, output_file)

    # Check if the directory exists, and if not, create it
    if not os.path.exists(directory):
        os.makedirs(directory)
    if len([name for name in os.listdir(directory) if name.endswith('.png')]) > 3:
        # Avoid overloading file system with images
        print('***QUEUE FULL***')
        print('***LOST FILE: {}***'.format(output_file))
        print('***WAITING 30 SECONDS BEFORE LISTENING***')
        time.sleep(30)
    else:
        # Save payload to file
        with open(full_path, 'wb') as f:
            f.write(payload)
        print('***SAVED IMAGE AS {}***'.format(full_path))
    sock.close()
    time.sleep(0.05)