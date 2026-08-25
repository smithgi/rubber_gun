import logging
import serial
import time
import math
import struct
import threading

logger = logging.getLogger(__name__)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtCore import QObject  # Add this import

from config import RADAR_PORT


# Single-Target Detection Commands
Single_Target_Detection_CMD = b'\xFD\xFC\xFB\xFA\x02\x00\x80\x00\x04\x03\x02\x01'
# Multi-Target Detection Command
Multi_Target_Detection_CMD = b'\xFD\xFC\xFB\xFA\x02\x00\x90\x00\x04\x03\x02\x01'

ACK_RESPONSE = b'\xFD\xFC\xFB\xFA\x00\x00\x00\x00\x02\x00\x04\x03\x02\x01'

DEBUG = True

class RD03D(QObject):
    item_added = pyqtSignal(float, float, float, float)  # Signal to communicate with main.py

    def __init__(self):
        super().__init__()
        self.ser = serial.Serial(
            port=RADAR_PORT,
            baudrate=256000,
            timeout=1
        )
        self.alarm_stream_data = ""

    def read_data(self):
        while True:
            if self.ser.in_waiting > 0:
                data = self.ser.read(self.ser.in_waiting)
                if len(data) == 30:
                    self.process_data(data)


    def process_data(self, data):
        #print(data)
        """Parse the received radar data frame."""
        if len(data) < 12:
            logger.warning("Invalid frame length")
            return


        rx_count = len(data)
        if rx_count >= 30:
            # Extract data for Target 1
            target1_x, target1_y, target1_speed, target1_distance_res = struct.unpack('<hhHH', bytes(data[4:12]))
            
            #target1_x = struct.unpack('<h', data[4:6])
            #target1_x = struct.unpack('<h', data[4:6])[0]
            #target1_y = struct.unpack('<h', data[7:9])[0]
            target1_y = target1_y - 130
            if target1_y < 0:
                target1_y += 32768
            if target1_x < 0:
                target1_x += 32768
                target1_x = 0 - target1_x
            target1_speed -= 0x10
            target1_distance_res = hex(target1_distance_res)
            target1_distance = math.sqrt(target1_x**2 + target1_y**2)
            target1_angle = math.atan2(target1_y, target1_x) * 180.0 / math.pi

            #print(f"\r\nTarget 1 - Distance: {target1_distance / 10.0:.1f} cm, Angle: {target1_angle:.1f} degrees, X: {target1_x} mm, Y: {target1_y} mm, Speed: {target1_speed} cm/s, Distance Resolution: {target1_distance_res} mm")
            stream_data_line = f"Target 1 - Distance: {target1_distance / 10.0:.1f} cm, Angle: {target1_angle:.1f} degrees, X: {target1_x} mm, Y: {target1_y} mm, Speed: {target1_speed} cm/s, Distance Resolution: {target1_distance_res} mm"
            self.alarm_stream_data += stream_data_line + "\n"
            #print(stream_data_line)

            if 'last_x' not in locals():
                last_x = 0
                last_y = 0

            #if last_x != target1_x or last_y != target1_y:
            #    self.radar_interface.remove_target(last_x, last_y)

            

            last_x = target1_x
            last_y = target1_y


            current_time = time.time()
            if not hasattr(self, 'last_alarm_time'):
                self.last_alarm_time = 0

            #print("Target 1 - ",target1_x, target1_y, target1_distance, target1_angle)

            #self.item_added.emit(target1_x, target1_y, target1_distance, target1_angle)
            
            self.item_added.emit(target1_x, target1_y, target1_distance, target1_angle)

            #print(target1_x, target1_y, target1_distance, target1_angle)
            if current_time - self.last_alarm_time >= 10:
                logger.info("Sending to agent")
                #threading.Thread(target=self.send_to_agent, args=(self.alarm_stream_data,), daemon=True).start()
                
                if DEBUG:
                    logger.debug("Target 1 - %s %s %s %s", target1_x, target1_y, target1_distance, target1_angle)
                #print(target1_x, target1_y, target1_distance, target1_angle)
                
                
                #self.add_target_to_radar_interface(target1_x, target1_y, target1_distance, target1_angle)
                #self.radar_interface.add_target(target1_x, target1_y, target1_distance, target1_angle)
                self.last_alarm_time = time.time()
                self.alarm_stream_data = ""

    def start(self):
        self.read_data()

    def send_command(self, command):
        logger.debug("Sending command: %s", command.hex())
        self.ser.write(command)
        self.wait_for_ack()

    """
    def wait_for_ack(self):
        return
        # Wait for an acknowledgment from the radar module.
        ack_received = False
        while not ack_received:
            if self.ser.in_waiting > 0:
                data = self.ser.read(self.ser.in_waiting)
                #(f"Received: {data.hex()}")
                #print(f"ACK_RESPONSE: {ACK_RESPONSE.hex()}")
                if ACK_RESPONSE in data:
                    print("ACK received")
                    self.stop()
                    ack_received = True
                    print("Acknowledgment received from radar module.")
                    break
    """

    def send_to_agent(self, data):
        pass
        #self.alarm_agent.check_status(data)


if __name__ == "__main__":
    rd03d = RD03D()
    rd03d.start()