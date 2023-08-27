from flask import *
from flask_cors import CORS
from scapy.all import *
import socket, os, json, argparse
from datetime import datetime

app = Flask(__name__)
CORS(app)
VERSION = '1.0.0' # Not currently displayed and version does not correlate to control apps

@app.route('/ttc', methods=['GET'])
def get_ttc():
    with open('data/ttc.json', 'r') as f:
        ttc_data = json.load(f)
    
    # Sort time_data in descending order by current_time
    ttc_data['time_data'] = sorted(ttc_data['time_data'], key=lambda x: x['current_time'], reverse=True)

    # Sort mode_data in descending order by decoded_time
    ttc_data['mode_data'] = sorted(ttc_data['mode_data'], key=lambda x: x['decoded_time'], reverse=True)

    return jsonify(ttc_data)

def command_write(cmd_type, dst_ip):
    dst_port = 7474

    # Load the current data from file or initialize with default structure
    default_data = {
        'time_data': [],
        'mode_data': []
    }

    file_path = 'data/ttc.json'
    max_size = 5 * 1024 * 1024  # 5MB

    try:
        # Check if file size is greater than 5MB
        if os.path.getsize(file_path) > max_size:
            os.remove(file_path)
            with open(file_path, 'w') as f:
                json.dump(default_data, f)
            data = default_data
        else:
            with open(file_path, 'r') as f:
                data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = default_data
        

    if cmd_type == 'mode':
        ## Mode Status Packet Command
        ## Note: This packet is sent randomly every 1-10 minutes
        SLP_EFP_DC    = 1 << 0  # b0
        SLP_SWEEP_OFF = 1 << 1  # b1
        WAVE_OFF      = 1 << 2  # b2
        SIP_SWEEP_OFF = 1 << 3  # b3
        SIP_TRACK_OFF = 1 << 4  # b4
        current_science_mode = random.randint(0,16)

        # 32 bit unsigned integer / 2
        system_clock_milliseconds = int(time.time() * 1000)

        # The current time is larger than 32 bits, wrapping to have the current time fit
        wrapped_time = system_clock_milliseconds % (2**32)

        # Packing data
        packed_data = struct.pack('>BI', current_science_mode, wrapped_time)

        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Send data
        print('***TTC: SENDING MODE PACKET***')
        sock.sendto(packed_data, (dst_ip, dst_port))

        # Create a mapping of modes to their names
        science_modes = {
            SLP_EFP_DC: 'SLP_EFP_DC',
            SLP_SWEEP_OFF: 'SLP_SWEEP',
            WAVE_OFF: 'WAVE',
            SIP_SWEEP_OFF: 'SIP_SWEEP',
            SIP_TRACK_OFF: 'SIP_TRACK'
        }

        mode_status = {}

        for mode, name in science_modes.items():
            status = 'ON' if (current_science_mode & mode) == 0 else 'OFF'
            mode_status[name] = status

        # Decoding
        current_time_seconds = int(time.time())
        decoded_time_milliseconds = (current_time_seconds * 1000 & ~(2**32 - 1)) | wrapped_time
        decoded_time = datetime.fromtimestamp(decoded_time_milliseconds / 1000.0)
        
        # Create a dictionary to store all the data to be written to the file
        data_to_save = {
            'mode_status': mode_status,
            'decoded_time': decoded_time.strftime('%Y-%m-%d %H:%M:%S')  # Convert datetime object to string
        }

        data['mode_data'].append(data_to_save)
        with open('data/ttc.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)

    elif cmd_type == 'time':
        ## Status Packet Correlated Timestamp
        ## Note: This packet is sent every 2 minutes
        # Get current date and time
        now = datetime.now()
        # Extract all the required components
        pps_system_clock_milliseconds = now.microsecond // 1000
        pps_rtc_seconds = now.second
        pps_rtc_hundredths = now.microsecond // 10000
        pps_rtc_hours = now.hour
        pps_rtc_minutes = now.minute
        pps_rtc_months = now.month
        pps_rtc_date = now.day
        pps_rtc_years = now.year - 2000  # Assuming the year is represented in 2 digits (e.g., 23 for 2023)
        pps_rtc_weekdays = now.weekday()  # Monday is 0 and Sunday is 6

        # Without a GPS data source, just setting to random 16 bit unsigned integer
        gps_week_number = random.randint(0,65535)
        pps_gps_milliseconds = random.randint(0,65535)

        # Pack the data
        data_string = struct.pack(
            '>I BB BB BB BB H I',  # Format string for the data
            pps_system_clock_milliseconds,
            pps_rtc_seconds, pps_rtc_hundredths,
            pps_rtc_hours, pps_rtc_minutes,
            pps_rtc_months, pps_rtc_date,
            pps_rtc_years, pps_rtc_weekdays,
            gps_week_number,
            pps_gps_milliseconds
        )

        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Send data
        print('***TTC: SENDING STATUS PACKET***')
        sock.sendto(data_string, (dst_ip, dst_port))

        # Optionally close the socket if not sending more data
        sock.close()

        # Save the data to local JSON file
        now = datetime.now()
        format_now = now.strftime('%Y-%m-%d %H:%M:%S')
        data_dict = {
            'current_time': format_now,
            'pps_system_clock_milliseconds': pps_system_clock_milliseconds,
            'pps_rtc_seconds': pps_rtc_seconds,
            'pps_rtc_hundredths': pps_rtc_hundredths,
            'pps_rtc_hours': pps_rtc_hours,
            'pps_rtc_minutes': pps_rtc_minutes,
            'pps_rtc_months': pps_rtc_months,
            'pps_rtc_date': pps_rtc_date,
            'pps_rtc_years': pps_rtc_years,
            'pps_rtc_weekdays': pps_rtc_weekdays,
            'gps_week_number': gps_week_number,
            'pps_gps_milliseconds': pps_gps_milliseconds
        }

        data['time_data'].append(data_dict)

        with open('data/ttc.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)

def mode_task(dst_ip):
    while True:
        cmd_type = 'mode'
        command_write(cmd_type, dst_ip)
        time.sleep(random.randint(60,600))

def time_task(dst_ip):
    while True:
        cmd_type = 'time'
        command_write(cmd_type, dst_ip)
        time.sleep(120)

@app.route('/sosi', methods=['GET'])
def get_sosi():
    sosi_data = []

    with open('data/sosi_store.tle', 'r') as f:
        for line in f:
            try:
                sosi_data.append(json.loads(line.strip()))
            except json.JSONDecodeError as e:
                print('Error parsing line: {}'.format(e))
    
    # Sort the data by timestamp
    sorted_sosi_data = sorted(sosi_data, key=lambda x: x['timestamp'], reverse=True)

    return jsonify({
        'sosi_data': sorted_sosi_data,
        })

def track_store(stop_event):
    host = '0.0.0.0'  # Listen on all available network interfaces
    port = 7074
    HEADER_FORMAT = '!4s4sBBIH'
    header_length = struct.calcsize(HEADER_FORMAT)
    
    # Create a socket object and bind it to the specified host and port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port)) 

    print(f'***SOSI: Listening for UDP traffic on port {port}***')

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
        print(f'Error while receiving data: {e}')
    except KeyboardInterrupt:
        pass
    finally:
        # Close the socket
        sock.close()
        print('Listener thread stopped.')

@app.route('/imagery', methods=['GET'])
def get_imagery():
    image_dir = 'images'  # The directory containing the images

    # Check if the image directory exists
    if not os.path.exists(image_dir):
        return 'No image directory available', 404

    # List all files in the image directory
    files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]

    # If there are no files in the directory, return a message
    if not files:
        return 'No images available', 404

    # Sort the files by modification time
    files.sort(key=lambda x: os.path.getmtime(os.path.join(image_dir, x)))

    # Get the most recent file
    recent_image = files[-1]

    # Serve the most recent image
    return send_from_directory(image_dir, recent_image, as_attachment=False, mimetype='image/jpeg')

def image_store(stop_event):
    host = '0.0.0.0'  # Listen on all available network interfaces
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

    print(f'***IMAGERY: Listening for incoming images on port {port}***')
    try:
        while not stop_event.is_set():
            # Accept an incoming connection
            conn, addr = sock.accept()

            # Receive the file name and size
            file_info = conn.recv(buffer_size).decode()
            try:
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

                print(f'Received and saved image: {file_path} from {addr}')

                # Close the connection
                conn.close()

                # Check if there are more than 5 files in the image_dir
                files = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
                if len(files) > 5:
                    # Get the oldest file
                    oldest_file = min(files, key=lambda x: os.path.getctime(os.path.join(image_dir, x)))
                    # Log the oldest file's name
                    image_log = 'images/recv_imagery.log'
                    if not os.path.exists(image_log):
                        with open(image_log, 'w') as log_file:
                            log_file.write(f"Deleted {oldest_file} due to space constraints\n")
                    else:
                        with open(image_log, 'a') as log_file:
                            log_file.write(f"Deleted {oldest_file} due to space constraints\n")
                    # Delete the oldest file
                    os.remove(os.path.join(image_dir, oldest_file))
                    print(f"Deleted {oldest_file} due to space constraints")

            except ValueError:
                print("Invalid file info received.")
                conn.close()
                continue
            
    except OSError as e:
        print(f'Error while receiving image: {e}')
    except KeyboardInterrupt:
        pass
    finally:
        # Close the socket
        sock.close()
        print('Image store thread stopped.')

@app.route('/')
def home():
    # Variables
    sosi_update = ''
    imagery_update = ''
    imagery_dir = 'images'
    ttc_update = ''

    # Initialize the last updated sosi time when refreshing the page.
    sosi_path = 'data/sosi_store.tle'
    timestamp = os.path.getmtime(sosi_path)
    sosi_update = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    # Initialize the last updated imagery time when refreshing the page.
    # Get a list of all files in the directory
    files = [f for f in os.listdir(imagery_dir) if os.path.isfile(os.path.join(imagery_dir, f))]
    
    # Find the most recently updated file
    most_recent_file = max(files, key=lambda file: os.path.getmtime(os.path.join(imagery_dir, file)))

    # Get the datetime when imagery was last updated
    timestamp = os.path.getmtime(os.path.join(imagery_dir, most_recent_file))
    imagery_update = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    # Initialize the last updated sosi time when refreshing the page.
    ttc_path = 'data/ttc.json'
    timestamp = os.path.getmtime(ttc_path)
    ttc_update = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    return render_template('index.html', sosi_update=sosi_update, imagery_update=imagery_update, ttc_update=ttc_update)

if __name__ == '__main__':
    # Initialize menu
    parser = argparse.ArgumentParser(description='Start OrbitLink and start sending and receiving SOSI, TTC, and Imagery data')
    parser.add_argument('-ttc', '--ttc_host', required=True, type=str, help='the destination IP address of the TTC host')
    parser.add_argument('--headless', action='store_true', help='run the app in headless mode (only Flask server)')

    try:
        args = parser.parse_args()
    except Exception as e:
        print('Error with {}'.format(e))

    # Create an Event object to signal the listener thread to stop
    stop_event = threading.Event()

    # Only run the listener threads if not in headless mode
    if not args.headless:
        # Start listener in a background thread for SOSI tracks
        listener_thread = threading.Thread(target=track_store, args=(stop_event,))
        listener_thread.start()

        # Start listener in a background thread for Imagery
        image_store_thread = threading.Thread(target=image_store, args=(stop_event,))
        image_store_thread.start()

        # Start a sender for TTC
        # Define distant TTC receiver
        dst_ip = args.ttc_host
        mode_thread = threading.Thread(target=mode_task, args=(dst_ip,))
        mode_thread.start()
        time.sleep(2)

        time_thread = threading.Thread(target=time_task, args=(dst_ip,))
        time_thread.start()
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print('CTRL+C detected. Shutting down...')
    finally:
        # Give the thread some time to finish its work
        stop_event.set()
        time.sleep(1)
        print('Terminating the program...')
        os._exit(1)