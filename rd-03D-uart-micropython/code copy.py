# MicroPython Code for RD-03D (RP2040 Zero)
# Multi-Target + Single Target Toggle via Serial Command

import board
import busio
import time
import struct
import math


# Initialize UART at 256000 baud (debug and tracking mode)
uart = busio.UART(board.GP0, board.GP1, baudrate=256000, timeout=0.1)

# --- Command definitions ---
CMD_OPEN_MODE = bytes([0xFD, 0xFC, 0xFB, 0xFA, 0x04, 0x00, 0xFF, 0x00, 0x01, 0x00, 0x04, 0x03, 0x02, 0x01])
CMD_CLOSE_MODE = bytes([0xFD, 0xFC, 0xFB, 0xFA, 0x02, 0x00, 0xFE, 0x00, 0x04, 0x03, 0x02, 0x01])

# Switch to single target mode (custom command assumed as per manual)
CMD_SINGLE_TARGET_MODE = bytes([0xAA, 0x01, 0x01, 0x55])  # Placeholder, adjust if actual command found
# Switch to multi-target mode (custom command assumed as per manual)
CMD_MULTI_TARGET_MODE = bytes([0xAA, 0x01, 0x03, 0x55])  # Placeholder, adjust if actual command found

# Send a command over UART with a brief wait
def send_cmd(cmd, wait=0.1):
    print("Sendign command:")
    print(cmd)
    uart.write(cmd)
    time.sleep(wait)

def decode_signed_15bit(raw):
    sign = (raw & 0x8000) >> 15
    value = raw & 0x7FFF
    return value if sign else -value

# Parse a target frame (16 bytes)
def parse_target(data):
    raw_x = struct.unpack_from('<H', data, 0)[0]
    raw_y = struct.unpack_from('<H', data, 2)[0]
    raw_speed = struct.unpack_from('<H', data, 4)[0]
    distance = struct.unpack_from('<H', data, 6)[0]

    x = decode_signed_15bit(raw_x)
    y = decode_signed_15bit(raw_y)
    speed = decode_signed_15bit(raw_speed)

    return x, y, speed, distance

# Detect and parse a complete multi-target frame (up to 3 targets)
def parse_multi_target_frame(buf):
    header = b'\xAA\xFF\x03\x00'
    tail = b'\x55\xCC'
    start = buf.find(header)
    if start != -1:
        end = buf.find(tail, start)
        if end != -1 and end - start >= 26:
            frame = buf[start + 4:end]
            for i in range(3):
                t = frame[i * 8:(i + 1) * 8]
                if t != b'\x00' * 8:
                    x, y, speed, dist = parse_target(t)
                    print(f"Target {i+1}: x={x} mm, y={y} mm, speed={speed} cm/s, distance={dist} mm")
            return end + 2  # skip tail
    return -1

# Setup radar in desired mode (single or multi target)
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



# Main logic
print("Starting")

setup_radar(single_target=False)  # Change to True to use single target mode

buf = bytearray()
while True:
    if uart.in_waiting:
        data = uart.read(64)
        if data:
            buf.extend(data)
            if len(buf) > 512:
                buf = buf[-512:]
            while True:
                parsed_end = parse_multi_target_frame(buf)
                if parsed_end == -1:
                    break
                else:
                    buf = buf[parsed_end:]
    time.sleep(0.05)