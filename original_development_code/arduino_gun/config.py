"""Load port configuration from ../.env."""
import logging
import os

from dotenv import load_dotenv

try:
    # Explicitly specify the .env path in the parent directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, ".env")
    load_dotenv(env_path)
except ImportError:
    pass

SERVO_PORT = os.getenv("SERVO_PORT", "/dev/ttyUSB0")
RADAR_PORT = os.getenv("RADAR_PORT", "/dev/ttyACM0")
GUN_H_CALIBRATION = int(os.getenv("GUN_H_CALIBRATION", "0"))
GUN_V_CALIBRATION = int(os.getenv("GUN_V_CALIBRATION", "0"))
BURST_NUM = int(os.getenv("BURST_NUM", "3"))

_LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
LOG_LEVEL = _LOG_LEVELS.get(
    os.getenv("DEBUG_LEVEL", "INFO").upper(),
    logging.INFO,
)
