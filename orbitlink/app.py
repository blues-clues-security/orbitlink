from flask import *
from flask_cors import CORS
from scapy.all import *
import socket

app = Flask(__name__)
CORS(app)

@app.route('/ttc', methods=['GET'])
def get_ttc():
    with open("data/ttc.json", "r") as f:
        ttc_data = json.load(f)

    return jsonify({
        'ttc_data': ttc_data,
        })

@app.route('/sosi', methods=['GET'])
def get_sosi():
    sosi_data = []

    with open("data/sosi_store.tle", "r") as f:
        for line in f:
            try:
                sosi_data.append(json.loads(line.strip()))
            except json.JSONDecodeError as e:
                print("Error parsing line: {}".format(e))
        
    return jsonify({
        'sosi_data': sosi_data,
        })

def track_store(stop_event):
    host = "192.168.0.47"  # Listen on all available network interfaces
    port = 7074
    HEADER_FORMAT = '!4s4sBBIH'
    header_length = struct.calcsize(HEADER_FORMAT)
    
    # Create a socket object and bind it to the specified host and port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port)) 

    print(f"***SOSI TRACKS: Listening for UDP traffic on port {port}***")

    try:
        while not stop_event.is_set():
            # Receive up to 4096 bytes of data from the client
            data, addr = sock.recvfrom(4096)

            # Unpack the header
            header_data = data[:header_length]
            src_ip, dest_ip, protocol_id, sequence_number, timestamp, payload_length = struct.unpack(HEADER_FORMAT, header_data)

            # Extract and decode the payload as UTF-8
            payload_data = data[header_length:header_length+payload_length]
            payload_text = payload_data.decode('utf-8')

            # Prepare the data for JSON
            record = {
                # Convert from epoch time
                'timestamp': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                'src_ip': socket.inet_ntoa(src_ip),
                'dest_ip': socket.inet_ntoa(dest_ip),
                'protocol_id': protocol_id,
                'sequence_number': sequence_number,
                'payload': payload_text,
            }

            # Write the data to sosi_store.tle
            with open('data/sosi_store.tle', 'a') as file:
                json.dump(record, file)
                file.write('\n')
    except OSError as e:
        print(f"Error while receiving data: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        # Close the socket
        sock.close()
        print("Listener thread stopped.")

@app.route('/imagery', methods=['GET'])
def get_imagery():
    image_dir = 'images'  # The directory containing the images

    # Check if the image directory exists
    if not os.path.exists(image_dir):
        return "No image directory available", 404

    # List all files in the image directory
    files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]

    # If there are no files in the directory, return a message
    if not files:
        return "No images available", 404

    # Sort the files by modification time
    files.sort(key=lambda x: os.path.getmtime(os.path.join(image_dir, x)))

    # Get the most recent file
    recent_image = files[-1]

    # Serve the most recent image
    return send_from_directory(image_dir, recent_image, as_attachment=False, mimetype='image/jpeg')

def image_store(stop_event):
    host = "192.168.0.47"  # Listen on all available network interfaces
    port = 8069  # The port to listen on
    buffer_size = 1024  # The size of the buffer used to receive data
    image_dir = 'images'  # The directory to save received images

    # Check if the image directory exists, and if not, create it
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    # Create a socket object and bind it to the specified host and port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))

    # Listen for incoming connections
    sock.listen(5)

    print(f"***IMAGE STORE: Listening for incoming images on port {port}***")

    try:
        while not stop_event.is_set():
            # Accept an incoming connection
            conn, addr = sock.accept()

            # Receive the file name and size
            file_info = conn.recv(buffer_size).decode()
            file_name, file_size = file_info.split('|')
            file_size = int(file_size)
            file_path = os.path.join(image_dir, file_name)

            # Receive and save the image data
            with open(file_path, 'wb') as image_file:
                bytes_received = 0
                while bytes_received < file_size:
                    data = conn.recv(min(buffer_size, file_size - bytes_received))
                    if not data:
                        break
                    image_file.write(data)
                    bytes_received += len(data)

            print(f"Received and saved image: {file_path}")

            # Close the connection
            conn.close()
    except OSError as e:
        print(f"Error while receiving image: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        # Close the socket
        sock.close()
        print("Image store thread stopped.")

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    # Create an Event object to signal the listener thread to stop
    stop_event = threading.Event()

    # Start listener in a background thread for SOSI tracks
    listener_thread = threading.Thread(target=track_store, args=(stop_event,))
    listener_thread.start()

    # Start listener in a background thread for Imagery
    image_store_thread = threading.Thread(target=image_store, args=(stop_event,))
    image_store_thread.start()

    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        pass
    finally:
        # Give the thread some time to finish its work
        stop_event.set()
        time.sleep(1)
        print("Terminating the program...")
        os._exit(1)
            