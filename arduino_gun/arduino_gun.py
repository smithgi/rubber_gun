import logging
import serial
import json
import sys
import time
from config import SERVO_PORT

logger = logging.getLogger(__name__)


class ArduinoGun:
    def __init__(self, port=None, baudrate=115200):
        port = port or SERVO_PORT
        self.ser = serial.Serial(port, baudrate)

    def move(self, h=0, v=0):
        if h > 180:
            logger.error("Horizontal angle 'h' cannot be greater than 180. Received h=%s", h)
            return False
        """Move gun to horizontal (h) and vertical (v) angles in degrees."""
        cmd = {"h": int(h), "v": int(v)}
        self.ser.write((json.dumps(cmd) + "\n").encode("ascii"))
        logger.debug("Sent command: %s", cmd)
        response = self.ser.readline().decode("ascii").strip()
        logger.debug("Response: %s", response)
        return json.loads(response)

    def shoot(self):
        """Fire the trigger servo (Arduino expects {\"shoot\":true})."""
        self.ser.write(b'{"shoot":true}\n')
        logger.info("Sent shoot command")
        response = self.ser.readline().decode("ascii").strip()
        logger.info("Response: %s", response)
        return json.loads(response)

    def burst_shoot(self, count=3):
        """Fire the trigger servo (Arduino expects {\"shoot\":true})."""
        for _ in range(count):
            self.ser.write(b'{"shoot":true}\n')
            logger.info("Sent shoot command")
            response = self.ser.readline().decode("ascii").strip()
            logger.info("Response: %s", response)
            time.sleep(0.3)
        # return the last response
        return json.loads(response)

    def close(self):
        self.ser.close()


if __name__ == "__main__":
    from config import LOG_LEVEL
    logging.basicConfig(level=LOG_LEVEL)

    h = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    v = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    gun = ArduinoGun()
    gun.move(h=h, v=v)
    logger.info("Gun response: %s", gun.move(h=h, v=v))
    gun.close()
