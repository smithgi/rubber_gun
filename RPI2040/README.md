# RP2040 standalone radar gun

Runs the whole stack on one RP2040 (RP2040-Zero / Pico):

- talk to the RD-03D on UART
- aim `TURN` + `UP` servos
- fire the `TRIGGER` servo

The Python host (`main.py`) and the ESP32 sketch (`arduino_gun.ino`) are not needed.

Copy `code.py` onto the CircuitPython `CIRCUITPY` drive.

## Pin map

| Function | RP2040 pin | Goes to |
|---|---|---|
| Radar TX | GP0 | RD-03D **RX** |
| Radar RX | GP1 | RD-03D **TX** |
| Turn servo (h) | GP2 | Turn servo **SIG** (orange) |
| Up servo (v) | GP3 | Up servo **SIG** (orange) |
| Trigger servo | GP4 | Trigger servo **SIG** (orange) |
| Common ground | GND | PSU GND + radar GND + all 3 servo GND |
| Servo / radar power | external **5V** | radar VCC + all 3 servo VCC (red) |

See `wiring.svg` and `wiring.png`.

## Wiring sketch

```
                    USB-C (powers the RP2040 only)
                         │
                         ▼
                   ┌─────────────┐
  RD-03D TX ──────►│ GP1  RX     │
  RD-03D RX ◄──────│ GP0  TX     │
                   │             │ GP2 ── SIG ── TURN servo
                   │ RP2040-Zero │ GP3 ── SIG ── UP servo
                   │             │ GP4 ── SIG ── TRIGGER servo
                   │ GND         │
                   └──────┬──────┘
                          │
     common GND ──────────┼────────── PSU GND
                          │
     5V PSU (≥2A) ── +5V ─┴── radar VCC + 3× servo VCC (red)

     Every brown/black servo wire → the same GND star.
     Do not power servos from the RP2040 3.3V pin.
```

UART names are crossed on purpose: module TX goes to MCU RX.

## Power

- Keep the RP2040 on USB-C.
- Power the three servos (and the RD-03D VCC) from a **separate 5 V supply, 2 A or more**.
- Tie all grounds together. Without a common GND the PWM signals will not reference the servos.

## Aim / shoot (same as `main.py`)

```
v = distance_mm / 100 + GUN_V_CALIBRATION
h = 180 - radar_angle + GUN_H_CALIBRATION
```

If the radar angle changes, the gun aims. If the next frame reports the same angle, it fires a burst.

Defaults match `.env`: `GUN_H_CALIBRATION=-30`, `GUN_V_CALIBRATION=-10`, `BURST_NUM=2`. Edit the constants at the top of `code.py`.

## USB serial (optional)

115200-style CircuitPython REPL / serial monitor:

| Command | Effect |
|---|---|
| `start` or `{"start":true}` | enable auto aim/shoot |
| `stop` or `{"stop":true}` | disable auto aim/shoot |
| `{"h":90,"v":40}` | manual aim |
| `{"shoot":true}` | one trigger pull |
| `{"trigger_pos":50}` | set trigger servo degrees |

Radar frames still print as JSON arrays, same as the old RP2040 bridge.
