# CircuitPython: RD-03D radar + 3-servo gun on one RP2040 (e.g. RP2040-Zero)
# Replaces the Python host + ESP32 servo board.

import board
import busio
import json
import math
import struct
import supervisor
import time
import pwmio

# ---------------------------------------------------------------------------
# Pin map  (see wiring.svg / README.md)
# ---------------------------------------------------------------------------
# Radar UART (same as the previous RP2040 bridge)
RADAR_TX_PIN = board.GP0  # RP2040 TX  ->  RD-03D RX
RADAR_RX_PIN = board.GP1  # RP2040 RX  <-  RD-03D TX

# Servos  (PWM, 50 Hz)
TURN_SERVO_PIN = board.GP2     # horizontal / "h"
UP_SERVO_PIN = board.GP3       # vertical   / "v"
TRIGGER_SERVO_PIN = board.GP4

# ---------------------------------------------------------------------------
# Calibration  (from .env: GUN_H_CALIBRATION, GUN_V_CALIBRATION, BURST_NUM)
# ---------------------------------------------------------------------------
GUN_H_CALIBRATION = -20
GUN_V_CALIBRATION = -10
BURST_NUM = 2

TRIGGER_FIRE_DEG = 50
TRIGGER_IDLE_DEG = 0
TRIGGER_HOLD_S = 0.5
BURST_GAP_S = 0.3

UP_START_DEG = 0
TURN_START_DEG = 90
SERVO_HOME_STEP_S = 0.01

GUN_ENABLED_ON_BOOT = True
RADAR_SINGLE_TARGET = False
RADAR_BAUD = 256000

# ---------------------------------------------------------------------------
# Radar protocol
# ---------------------------------------------------------------------------
CMD_OPEN_MODE = bytes(
    [0xFD, 0xFC, 0xFB, 0xFA, 0x04, 0x00, 0xFF, 0x00, 0x01, 0x00, 0x04, 0x03, 0x02, 0x01]
)
CMD_CLOSE_MODE = bytes(
    [0xFD, 0xFC, 0xFB, 0xFA, 0x02, 0x00, 0xFE, 0x00, 0x04, 0x03, 0x02, 0x01]
)
CMD_SINGLE_TARGET_MODE = bytes([0xAA, 0x01, 0x01, 0x55])
CMD_MULTI_TARGET_MODE = bytes([0xAA, 0x01, 0x03, 0x55])
FRAME_HEADER = b"\xAA\xFF\x03\x00"
FRAME_TAIL = b"\x55\xCC"

uart = busio.UART(RADAR_TX_PIN, RADAR_RX_PIN, baudrate=RADAR_BAUD, timeout=0.1)


class Servo:
    """Hobby servo on pwmio: 500-2400 us pulse, 50 Hz (matches ESP32Servo)."""

    def __init__(self, pin, min_us=500, max_us=2400):
        self.pwm = pwmio.PWMOut(pin, duty_cycle=0, frequency=50)
        self.min_us = min_us
        self.max_us = max_us
        self.angle = 90

    def write(self, angle):
        angle = max(0, min(180, int(angle)))
        span = self.max_us - self.min_us
        us = self.min_us + span * angle / 180.0
        self.pwm.duty_cycle = int(us / 20000.0 * 65535)
        self.angle = angle


turn_servo = Servo(TURN_SERVO_PIN)
up_servo = Servo(UP_SERVO_PIN)
trigger_servo = Servo(TRIGGER_SERVO_PIN)

gun_enabled = GUN_ENABLED_ON_BOOT
last_angle = None
radar_buf = bytearray()


def clamp_deg(value):
    return max(0, min(180, int(value)))


def move_smooth(servo, to_pos, step_s=SERVO_HOME_STEP_S):
    from_pos = servo.angle
    step = 1 if to_pos >= from_pos else -1
    for pos in range(from_pos, to_pos + step, step):
        servo.write(pos)
        time.sleep(step_s)
    servo.write(to_pos)


def fire_trigger():
    trigger_servo.write(TRIGGER_FIRE_DEG)
    time.sleep(TRIGGER_HOLD_S)
    trigger_servo.write(TRIGGER_IDLE_DEG)


def burst_shoot(count):
    for i in range(count):
        fire_trigger()
        if i < count - 1:
            time.sleep(BURST_GAP_S)


def drain_radar():
    global radar_buf
    while uart.in_waiting:
        uart.read(64)
    radar_buf = bytearray()


def move_gun(h, v):
    turn_servo.write(clamp_deg(h))
    up_servo.write(clamp_deg(v))


def aim_and_maybe_shoot(distance_mm, angle_deg):
    """Same policy as main.py handle_item_added."""
    global last_angle
    if not gun_enabled:
        return

    if last_angle != angle_deg:
        last_angle = angle_deg
        v = int(distance_mm / 100) + GUN_V_CALIBRATION
        h = 180 - angle_deg + GUN_H_CALIBRATION
        move_gun(h, v)
        print(json.dumps({"action": "aim", "h": clamp_deg(h), "v": clamp_deg(v), "angle": angle_deg}))
    else:
        print(json.dumps({"action": "burst", "angle": angle_deg, "count": BURST_NUM}))
        burst_shoot(BURST_NUM)
        drain_radar()


def send_cmd(cmd, wait=0.1):
    uart.write(cmd)
    time.sleep(wait)


def decode_signed_15bit(raw):
    sign = (raw & 0x8000) >> 15
    value = raw & 0x7FFF
    return value if sign else -value


def parse_target(data):
    raw_x = struct.unpack_from("<H", data, 0)[0]
    raw_y = struct.unpack_from("<H", data, 2)[0]
    raw_speed = struct.unpack_from("<H", data, 4)[0]
    distance_res = struct.unpack_from("<H", data, 6)[0]

    x = decode_signed_15bit(raw_x)
    y = decode_signed_15bit(raw_y)
    speed = decode_signed_15bit(raw_speed)

    distance = int(math.sqrt(x * x + y * y))
    angle = math.atan2(y, x) * 180.0 / math.pi
    return x, y, speed, distance_res, distance, angle


def parse_multi_target_frame(buf):
    start = buf.find(FRAME_HEADER)
    if start == -1:
        return -1
    end = buf.find(FRAME_TAIL, start)
    if end == -1 or end - start < 26:
        return -1

    frame = buf[start + 4 : end]
    target_data = []
    for i in range(3):
        t = frame[i * 8 : (i + 1) * 8]
        if t != b"\x00" * 8:
            x, y, speed, d_res, d_calc, angle = parse_target(t)
            target_data.append(
                {
                    "target": i + 1,
                    "x": x,
                    "y": y,
                    "speed": speed,
                    "distance_res": d_res,
                    "distance_calc": d_calc,
                    "angle": angle,
                }
            )

    if target_data:
        print(json.dumps(target_data))
        first = target_data[0]
        aim_and_maybe_shoot(first["distance_calc"], first["angle"])

    return end + 2


def setup_radar(single_target=True):
    send_cmd(CMD_OPEN_MODE)
    time.sleep(0.2)
    if single_target:
        send_cmd(CMD_SINGLE_TARGET_MODE)
        print("Switched to SINGLE target mode.")
    else:
        send_cmd(CMD_MULTI_TARGET_MODE)
        print("Switched to MULTI target mode.")
    time.sleep(0.2)
    send_cmd(CMD_CLOSE_MODE)
    print("Radar configuration complete.")


def setup_servos():
    turn_servo.write(90)
    up_servo.write(90)
    trigger_servo.write(TRIGGER_IDLE_DEG)
    move_smooth(up_servo, UP_START_DEG)
    move_smooth(turn_servo, TURN_START_DEG)
    time.sleep(0.2)


def handle_usb_command(line):
    global gun_enabled, last_angle
    raw = line.strip()
    if not raw:
        return

    text = raw.lower()
    if text in ("start", '{"start":true}', '{"start": true}'):
        gun_enabled = True
        last_angle = None
        print('{"gun":"running"}')
        return
    if text in ("stop", '{"stop":true}', '{"stop": true}'):
        gun_enabled = False
        last_angle = None
        print('{"gun":"stopped"}')
        return

    try:
        cmd = json.loads(raw)
    except ValueError:
        print('{"err":"invalid"}')
        return

    if cmd.get("start") is True:
        gun_enabled = True
        last_angle = None
        print('{"gun":"running"}')
        return
    if cmd.get("stop") is True:
        gun_enabled = False
        last_angle = None
        print('{"gun":"stopped"}')
        return

    h = cmd.get("h", cmd.get("H"))
    v = cmd.get("v", cmd.get("V"))
    trigger_pos = cmd.get("trigger_pos", cmd.get("TRIGGER_POS"))
    shoot = cmd.get("shoot", cmd.get("SHOOT")) is True

    if h is None and v is None and trigger_pos is None and not shoot:
        print('{"err":"invalid"}')
        return

    if h is not None and v is not None:
        move_gun(h, v)
        print(json.dumps({"h": turn_servo.angle, "v": up_servo.angle}))
    if trigger_pos is not None:
        trigger_servo.write(int(trigger_pos))
        print(json.dumps({"trigger_pos": trigger_servo.angle}))
    if shoot:
        fire_trigger()
        print('{"shoot":true}')


def poll_usb():
    if not supervisor.runtime.serial_bytes_available:
        return
    try:
        line = input()
    except Exception:
        return
    handle_usb_command(line)


def main():
    global radar_buf
    print("RP2040 radar+gun starting")
    setup_servos()
    setup_radar(single_target=RADAR_SINGLE_TARGET)
    print(json.dumps({"gun": "running" if gun_enabled else "stopped"}))

    while True:
        poll_usb()
        if uart.in_waiting:
            data = uart.read(64)
            if data:
                radar_buf.extend(data)
                if len(radar_buf) > 512:
                    radar_buf = radar_buf[-512:]
                while True:
                    parsed_end = parse_multi_target_frame(radar_buf)
                    if parsed_end == -1:
                        break
                    radar_buf = radar_buf[parsed_end:]
        time.sleep(0.01)


main()
