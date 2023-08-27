import socket
import struct
import time
import random
import threading
import json
import os
from datetime import datetime


def command_send(cmd_type):
    """Send data based on command type.
    
    Arguments:
    - cmd_type: Either 'mode' or 'time' which sends the appropriate TTC command.
    """
    # Destination IP and port for sending packets
    dst_ip = '169.254.10.254'  # This is sending data into the nethers of space
    dst_port = 7474

    # Default data structure for file storage
    default_data = {
        'time_data': [],
        'mode_data': []
    }

    # Attempt to load existing data or initialize with the default structure
    try:
        with open('ttc.json', 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open('ttc.json', 'w') as f:
            json.dump(default_data, f, indent=4)
        data = default_data.copy()
        

    if cmd_type == 'mode':
        # Constants for science mode status packet
        SLP_EFP_DC    = 1 << 0  # b0
        SLP_SWEEP_OFF = 1 << 1  # b1
        WAVE_OFF      = 1 << 2  # b2
        SIP_SWEEP_OFF = 1 << 3  # b3
        SIP_TRACK_OFF = 1 << 4  # b4

        # Generate random science mode
        current_science_mode = random.randint(0,16)

        # Get current time in milliseconds and wrap to fit 32 bits
        system_clock_milliseconds = int(time.time() * 1000)
        wrapped_time = system_clock_milliseconds % (2**32)

        # Pack the data for sending
        packed_data = struct.pack('>BI', current_science_mode, wrapped_time)

        # Send the packed data to the specified destination
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Send data
        print('PROCESS: SENDING MODE PACKET')
        sock.sendto(packed_data, (dst_ip, dst_port))

        # Decode the mode status and save to file
        science_modes = {
            SLP_EFP_DC: 'SLP_EFP_DC',
            SLP_SWEEP_OFF: 'SLP_SWEEP',
            WAVE_OFF: 'WAVE',
            SIP_SWEEP_OFF: 'SIP_SWEEP',
            SIP_TRACK_OFF: 'SIP_TRACK'
        }

        # Determine mode status (ON/OFF)
        mode_status = {name: 'ON' if (current_science_mode & mode) == 0 else 'OFF' for mode, name in science_modes.items()}

        # Decode the wrapped time
        current_time_seconds = int(time.time())
        decoded_time_milliseconds = (current_time_seconds * 1000 & ~(2**32 - 1)) | wrapped_time
        decoded_time = datetime.fromtimestamp(decoded_time_milliseconds / 1000.0)
        
        # Prepare data for saving to file
        data_to_save = {
            'mode_status': mode_status,
            'decoded_time': decoded_time.strftime('%Y-%m-%d %H:%M:%S')  # Convert datetime object to string
        }

        # Save the data to the JSON file
        data['mode_data'].append(data_to_save)
        with open('ttc.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)

    elif cmd_type == 'time':
        # Process and send status packet correlated timestamp
        # Extract current date and time details
        now = datetime.now()

        # Extract all the required components
        pps_system_clock_milliseconds = now.microsecond // 1000
        pps_rtc_seconds = now.second
        pps_rtc_hundredths = now.microsecond // 10000
        pps_rtc_hours = now.hour
        pps_rtc_minutes = now.minute
        pps_rtc_months = now.month
        pps_rtc_date = now.day
        pps_rtc_years = now.year - 2000
        pps_rtc_weekdays = now.weekday()

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
        print('PROCESS: SENDING STATUS PACKET')
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

        with open('ttc.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)

def mode_task(stop_event):
    """Send mode packets at random intervals between 1 and 10 minutes until stopped.
    
    Arguments:
    - stop_event: A threading event to signal when to stop listening.
    """
    while not stop_event.is_set():
        cmd_type = 'mode'
        command_send(cmd_type)
        time.sleep(random.randint(60,600))

def time_task(stop_event):
    """Send time packets every 2 minutes until stopped.
    
    Arguments:
    - stop_event: A threading event to signal when to stop listening.
    """
    while not stop_event.is_set():
        cmd_type = 'time'
        command_send(cmd_type)
        time.sleep(120)

def command_recv(stop_event):
    """Listen for incoming commands and log them.
    
    Arguments:
    - stop_event: A threading event to signal when to stop listening.
    """
    port = 7474
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('0.0.0.0', port))
    server_socket.setblocking(False)
    header = '>I BB BB BB BB H I'
    out_file = 'ttc_command_queue.log'
    print('LOG: Listening for commands on port {}...'.format(port))

    while not stop_event.is_set():  # Check stop_event periodically
        try:
            data, addr = server_socket.recvfrom(1024)  # buffer size is 1024 bytes
            print('LOG: Received data from {}'.format(addr))
            now = datetime.now()
            format_now = now.strftime('%Y-%m-%d %H:%M:%S')
            try:
                header = '>I BB BB BB BB H I'
                rec_data = struct.unpack(header, data)
            except:
                header = '>BI'
                rec_data = struct.unpack(header, data)
            finally:
                try:
                    with open(out_file, 'a') as f:
                        f.write('{} - Command: {} received from {}.\n'.format(format_now, rec_data, addr))
                except FileNotFoundError:
                    with open(out_file, 'w') as f:
                        f.write('{} - Command: {} received from {}.\n'.format(format_now, rec_data, addr))
        except BlockingIOError:
            time.sleep(0.1)
        except Exception as e:
            print('LOG: Error receiving data {}'.format(e))
    server_socket.close()


if __name__ == '__main__':
    """Main function to start sending mode and time packets and listen for incoming commands."""
    # Run commands at their specified times in a thread
    stop_event = threading.Event()
    try:
        mode_thread = threading.Thread(target=mode_task, args=(stop_event,))
        mode_thread.start()        
        time.sleep(2)

        time_thread = threading.Thread(target=time_task, args=(stop_event,))
        time_thread.start()        
        time.sleep(2)

        command_recv(stop_event)

    except (KeyboardInterrupt):
        print('LOG: Terminating the program...')
        stop_event.set()
        os._exit(1)