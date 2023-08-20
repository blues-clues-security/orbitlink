# import base64
# images = [1,2,3,4,5]
# for image in images:
#     with open("resources/image{}.png".format(image), "rb") as image_file:
#         image_data = image_file.read()

#     image_as_string = base64.b64encode(image_data).decode()


#     with open("resources/txt_image{}.txt".format(image), "w") as binary_image:
#         binary_image.write(image_as_string)

import socket, struct, datetime, json, os

host = "0.0.0.0"  # Listen on all available network interfaces
port = 6960
HEADER_FORMAT = '!4s4sBBIQ'
header_length = struct.calcsize(HEADER_FORMAT)

# Create a socket object and bind it to the specified host and port
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((host, port)) 

print("Listening for UDP traffic on port {}...".format(port))

# Continuously listen for incoming UDP traffic
try:
    # Receive up to 4096 bytes of data from the client
    data, addr = sock.recvfrom(4096)

    # Unpack the header
    header_data = data[:header_length]
    src_ip, dst_ip, protocol_id, sequence_number, timestamp, payload_length = struct.unpack(HEADER_FORMAT, header_data)

    # Extract and decode the payload as UTF-8
    payload_data = data[header_length:header_length+payload_length]
    payload_text = payload_data.decode('utf-8')

    # Write the data to sosi_store.tle
    with open("resources/recv_image{}.txt".format(sequence_number), "w") as binary_image:
        binary_image.write(payload_text)

except OSError as e:
    print("Error while receiving data: {}".format(e))

except KeyboardInterrupt:
    os._exit(1)

finally:
    print("Closing")