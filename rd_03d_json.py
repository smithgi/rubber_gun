import json
import logging
import time
import threading
import serial
from PyQt6.QtCore import QObject, pyqtSignal

from config import RADAR_PORT

logger = logging.getLogger(__name__)

class RD03DJson(QObject):
    item_added = pyqtSignal(float, float, float, float)  # x, y, distance, angle

    def __init__(self, port=None, baudrate=115200):
        port = port or RADAR_PORT
        super().__init__()
        self.running = True
        self.json_data = []
        
        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=1
            )
            logger.info("Connected to %s at %s baud", port, baudrate)
        except serial.SerialException as e:
            logger.error("Error opening serial port %s: %s", port, e)
            self.serial = None

    def read_data(self):
        """Reads JSON data from UART"""
        if not self.serial:
            logger.warning("Serial port not initialized")
            return

        buffer = ""
        while self.running:
            try:
                if self.serial.in_waiting:
                    # Read the full line from the serial port
                    line = self.serial.readline().decode('utf-8').strip()
                    logger.debug("Serial line: %s", line)
                    # Look for complete JSON arrays
                    if line.startswith('[') and line.endswith(']'):
                        try:
                            data = json.loads(line)
                            self.process_json_data(data)
                        except json.JSONDecodeError:
                            # If we can't decode, might be incomplete or malformed
                            logger.warning("JSON decode error, skipping line")

                time.sleep(0.01)  # Small delay to prevent CPU hogging

            except Exception as e:
                logger.error("Error reading from serial: %s", e)
                buffer = ""
                time.sleep(1)  # Wait before retrying

    def process_json_data(self, data):
        logger.debug("Processing JSON data: %s", data)
        """Process the JSON data and emit signals for each target"""
        try:
            for target in data:
                x = float(target['x'])
                y = float(target['y'])
                distance = float(target['distance_calc'])
                angle = float(target['angle'])
                
                # Emit the signal with the target data
                self.item_added.emit(x, y, distance, angle)
                
                logger.debug("Target detected: x=%s, y=%s, distance=%s, angle=%s", x, y, distance, angle)

        except Exception as e:
            logger.error("Error processing target data: %s", e)

    def send_command(self, command):
        """
        Send commands to the device if needed
        """
        if self.serial:
            try:
                self.serial.write(command.encode())
            except Exception as e:
                logger.error("Error sending command: %s", e)

    def stop(self):
        """Stop the data reading thread and close serial port"""
        self.running = False
        if self.serial:
            self.serial.close()

    def set_json_data(self, json_str):
        """
        Manual method to inject JSON data for testing
        """
        try:
            self.json_data = json.loads(json_str)
            self.process_json_data(self.json_data)
        except json.JSONDecodeError as e:
            logger.error("Error setting JSON data: %s", e)
