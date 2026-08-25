import logging
import serial
import struct
import math

from config import RADAR_PORT

logger = logging.getLogger(__name__)


# Configure the serial port
ser = serial.Serial(
    port=RADAR_PORT,
    baudrate=256000,
    timeout=1
)

def send_command(command_word, command_value):
    # Construct the frame
    frame_header = b'\xFD\xFC\xFB\xFA'
    frame_end = b'\x04\x03\x02\x01'
    data_length = struct.pack('<H', len(command_value) + 2)  # 2 bytes for command word
    command_word_bytes = struct.pack('<H', command_word)
    
    # Complete frame
    frame = frame_header + data_length + command_word_bytes + command_value + frame_end
    
    # Send the frame
    ser.write(frame)
    logger.debug("Sent: %s", frame.hex())

def read_uart_data():
    while True:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            #print(f"Received: {data.hex()}, {len(data)}")
            if len(data) == 30:
                process_data(data)

def process_data(data):
    if len(data) < 12:
        logger.warning("Invalid frame length")
        return

    if len(data) == 30:
        # Extract data for Target 1
        target1_x, target1_y, target1_speed, target1_distance_res = struct.unpack('<hhHH', data[4:12])
        target1_y -= 0x200
        target1_y -= 0x8000
        target1_speed -= 0x10
        target1_distance_res = hex(target1_distance_res)
        target1_distance = math.sqrt(target1_x**2 + target1_y**2)
        target1_angle = math.atan2(target1_y, target1_x) * 180.0 / math.pi

        logger.info("Target 1 - Distance: %.1f cm, Angle: %.1f degrees, X: %s mm, Y: %s mm, Speed: %s cm/s, Distance Resolution: %s mm",
                   target1_distance / 10.0, target1_angle, target1_x, target1_y, target1_speed, target1_distance_res)
# Example usage
# Command word for single target mode (example value, replace with actual)
command_word = 0x0008
# Command value for single target mode (example value, replace with actual)
command_value = b'\x00\x01'

send_command(command_word, command_value)
read_uart_data()