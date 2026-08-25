# Rubber-band radar gun

Standalone rubber-band turret: an RP2040 aims two servos from an RD-03D radar module and fires a third servo on a printed 5-shot slider gun.

Firmware lives in [`RPI2040/`](RPI2040/). Print files live in [`3dParts/`](3dParts/). The Python host and ESP32 sketch are not required.

## What you need

| Item | Notes |
|---|---|
| RP2040-Zero (or Pico) | USB-C powers the MCU only |
| RD-03D radar | UART to GP0 / GP1 |
| 3× micro servos | 9 g SG90 class. SG92R (or equivalent high-torque) is recommended for the trigger |
| External 5 V supply, **≥ 2 A** | Radar VCC + all three servo VCC. Do not power servos from the RP2040 3.3 V pin |
| Printed pan/tilt mount | [`3dParts/2axis_servo.3mf`](3dParts/2axis_servo.3mf) |
| Printed slider gun | [`3dParts/Slider Rubber Band Gun - 6731580/`](3dParts/Slider%20Rubber%20Band%20Gun%20-%206731580/) |
| Rubber bands | Up to 5 on the staircase muzzle |

## Print

### 2-axis servo mount

Open [`3dParts/2axis_servo.3mf`](3dParts/2axis_servo.3mf) in Bambu Studio (or another slicer that reads 3MF). The plate contains three parts:

| Part | Role |
|---|---|
| `base.stl` | Pan/tilt base |
| `HolderL.stl` | Left servo holder |
| `HolderR.stl` | Right servo holder |

The bundled slice is **0.20 mm Standard** on a **Bambu Lab A1**, 0.4 mm nozzle, textured PEI plate:

- Filament: PLA
- Layer height: 0.2 mm
- Walls: 2
- Infill: 15% zig-zag
- Top / bottom shells: 5 / 3
- Supports: tree (auto), slim
- Nozzle / bed: 220 °C / 65 °C

On another printer, match those settings as closely as you can. Print the holders with their flat faces on the bed.

### Slider rubber-band gun

Print the four STLs in [`3dParts/Slider Rubber Band Gun - 6731580/files/`](3dParts/Slider%20Rubber%20Band%20Gun%20-%206731580/files/):

| File | Role |
|---|---|
| `InnerPlate.stl` | Inner plate; servo mounts here |
| `OuterPlate.stl` | Outer plate |
| `TriggerPlate.stl` | Sliding trigger plate |
| `MuzzleRetainer.stl` | Retainer on the muzzle |

Same PLA / 0.2 mm settings work. Print the plates flat on the bed.

This gun is [Slider Rubber Band Gun by Kanten_Namako](https://www.thingiverse.com/thing:6731580) (CC BY-NC-SA). Photos of the assembled plates are in [`3dParts/Slider Rubber Band Gun - 6731580/images/`](3dParts/Slider%20Rubber%20Band%20Gun%20-%206731580/images/).

## Mechanical assembly

### Pan / tilt (TURN + UP)

1. Fit two SG90-class servos into `HolderL` and `HolderR`.
2. Mount the holders on `base` so one servo yaws (TURN, horizontal) and the other pitches (UP, vertical).
3. Attach the slider gun to the moving holder so the muzzle points forward.

On boot the firmware homes UP to `0°` and TURN to `90°`. Mount horns so those angles look like “level and centered.” If the turret is inverted or offset, change `GUN_H_CALIBRATION` and `GUN_V_CALIBRATION` in [`RPI2040/code.py`](RPI2040/code.py).

### Trigger gun

1. Fix the trigger servo on the **inner plate**.
2. Command the servo to **90°**, then attach a servo horn as in the Thingiverse photos.
3. Put the **trigger plate** on the inner plate, then attach the **outer plate**.
4. Attach the **muzzle retainer** to the muzzle.
5. Check motion by sweeping the servo from **90° to 120°**. That should release a band. If torque is weak, load fewer bands.
6. Load rubber bands from the **bottom** of the staircase to the **top**. Maximum five.

Firmware defaults are `TRIGGER_IDLE_DEG = 0` and `TRIGGER_FIRE_DEG = 50`. After the horn is locked at 90°, edit those two constants (or send `{"trigger_pos": …}` over USB) so idle holds the slider and fire matches the 90°→120° release.

## Firmware

1. Install [CircuitPython](https://circuitpython.org/) on the RP2040 so it mounts as `CIRCUITPY`.
2. Copy [`RPI2040/code.py`](RPI2040/code.py) onto that drive. No extra libraries are required (`board`, `busio`, `pwmio` are built in).
3. Leave the board on USB-C. Auto aim/shoot is on at boot (`GUN_ENABLED_ON_BOOT = True`).

Aim math (same policy as the old host):

```
v = distance_mm / 100 + GUN_V_CALIBRATION
h = 180 - radar_angle + GUN_H_CALIBRATION
```

If the radar angle changes, the gun aims. If the next frame reports the same angle, it fires a burst (`BURST_NUM = 2`).

## Wiring

Full diagram: [`RPI2040/wiring.svg`](RPI2040/wiring.svg) / [`RPI2040/wiring.png`](RPI2040/wiring.png).

| Function | RP2040 pin | Goes to |
|---|---|---|
| Radar TX | GP0 | RD-03D **RX** |
| Radar RX | GP1 | RD-03D **TX** |
| Turn servo (h) | GP2 | TURN servo **SIG** (orange / yellow) |
| Up servo (v) | GP3 | UP servo **SIG** (orange / yellow) |
| Trigger servo | GP4 | TRIGGER servo **SIG** (orange / yellow) |
| Common ground | GND | PSU GND + radar GND + all 3 servo GND (brown / black) |
| Servo / radar power | external **5 V** | radar VCC + all 3 servo VCC (red) |

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
     Do not power servos from the RP2040 3.3 V pin.
```

UART names are crossed on purpose: module TX goes to MCU RX. Radar baud is 256000.

### Power rules

1. Tie every GND together: PSU, RP2040, RD-03D, and all three servos. Without a common ground the PWM signals will not reference the servos.
2. Keep the RP2040 on USB-C. Power the three servos and the RD-03D VCC from the **separate 5 V, ≥ 2 A** supply.
3. Never feed servo VCC from the RP2040 3.3 V pin. Current spikes will brown-out the MCU.
4. 3.3 V PWM on GP2 / GP3 / GP4 is enough for most hobby servos.

## USB serial (optional)

Open the CircuitPython REPL / serial monitor:

| Command | Effect |
|---|---|
| `start` or `{"start":true}` | enable auto aim/shoot |
| `stop` or `{"stop":true}` | disable auto aim/shoot |
| `{"h":90,"v":40}` | manual aim |
| `{"shoot":true}` | one trigger pull |
| `{"trigger_pos":50}` | set trigger servo degrees |

Radar frames still print as JSON arrays.
