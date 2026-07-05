# Johnny 4 power distribution

How every board and load on Johnny 4 himself gets power: j4_receiver, j4_stepper_neck, j4_stepper_eyes, j4_talk, the PCA9685 servo bank, the WS2812B strip, the mouth LEDs, and the stepper drivers.

The controller side (j4_controller + the two XIAO displays) is not covered here; it runs off the TTGO's LiPo and USB.

## The rules

1. **Feed every logic board 5V into its 5V input and let its onboard regulator make the 3.3V.** Never inject 3.3V directly: that bypasses each board's regulator, brownout protection, and input protection, and backdrives the onboard LDO's output.
2. **Keep the twitchy loads off the logic buck.** Servos, the WS2812B strip, and the mouth LEDs get their own supplies so a servo stall or an LED flash never browns out a microcontroller mid-move.
3. **All grounds common.** Every buck output, the motor supplies, the LED rails, and the servo rail share ground with the boards. Signal without common ground is how you lose days (see j4_talk's header).

## Power tree

```
  MAIN BATTERY / SUPPLY
        |
        +-- motor rail (as-is, no buck) ------> 3x DM556TE ....... neck steppers
        |                                        (20-50VDC per the DM556TE manual)
        |                                  ----> 2x TMC2209 VM ... eye-pop steppers
        |                                        (4.75-29VDC)
        |
        +-- 12V rail ------------------------> j4_talk mouth-LED anodes
        |                                        (via the RFP30N06LE MOSFETs)
        |
        +-- BUCK 1: 5V / 3A "logic" ---------> j4_receiver ....... 5V header pin
        |                                ----> j4_stepper_neck ... chopped-USB VBUS
        |                                ----> 74AHCT125 x2 VCC .. (on neck board)
        |                                ----> j4_stepper_eyes ... chopped-USB VBUS
        |                                ----> j4_talk ........... VIN pin
        |                                        (cut the VUSB/VIN pad trace first)
        |
        +-- BUCK 2: 5V "LED" ----------------> WS2812B strip 5V
        |                                        (~60mA/LED full white; 30 LEDs ~ 1.8A;
        |                                         1000uF bulk cap at the injection point)
        |
        +-- BUCK 3: 5-6V "servo" ------------> PCA9685 V+ (servo power)
                                                 (13 servos; a stalled micro servo can
                                                  pull ~1A -- size generously, 5A+)

  PCA9685 VCC (logic) comes from j4_receiver's 3.3V pin as already wired.
  Every rail above shares GND with every board.
```

## Per-board feed points

| Board | Input | Where exactly | Notes |
|-------|-------|---------------|-------|
| j4_receiver (TTGO T-Display v1.1) | 5V header pin | Right rail, top (see pin diagram) | Shares the rail with USB VBUS; see flashing rules below |
| j4_stepper_neck (LOLIN32-Lite style) | USB-C port via chopped cable | Red = VBUS, black = GND, tape off green/white | These boards break out no 5V pin, so the USB port IS the 5V input; goes through the normal input path and regulator |
| j4_stepper_eyes (LOLIN32-Lite style) | USB-C port via chopped cable | Same as neck board | Same reasoning |
| j4_talk (Teensy 4.1) | VIN pin | Corner pin next to GND; accepts 3.6-5.5V | Cut the VUSB/VIN trace (two pads on the underside) before wiring this |
| 74AHCT125 x2 | VCC pin 14 | On the neck board | Same 5V line that feeds the neck board |
| PCA9685 servo power | V+ terminal | Screw terminal / V+ pin | From the servo buck, NOT the logic buck |
| PCA9685 logic | VCC pin | Already wired | From j4_receiver's 3.3V pin |
| WS2812B strip | 5V + GND at the strip | Own injection point | Data stays on receiver GPIO 25 through the ~330 ohm resistor |
| Mouth LEDs (j4_talk) | 12V rail | LED anodes via current-limit resistors | Switched low-side by the RFP30N06LE MOSFETs; Teensy only drives gates |

Do **not** feed 5V into any board's 3V3 pin, and do **not** feed the LOLIN32-Lite battery JST with 5V; that connector expects a 3.7V LiPo and runs through the charge circuit.

## USB flashing rules (backfeed)

Powering a board externally while its USB port is also connected puts two 5V sources on one rail. Handle each board like this:

- **j4_receiver (TTGO):** the 5V pin and USB VBUS are the same rail. Either unplug the buck feed before connecting USB to flash, or put a Schottky diode (e.g. SS34) in series with the buck feed so USB can't backfeed the buck.
- **j4_stepper_neck / j4_stepper_eyes:** the chopped USB cable occupies the port, so plugging in a programming cable means unplugging the power cable first. Self-solving. If you move the 5V feed to a soldered VBUS pad instead, add the same Schottky as the TTGO.
- **j4_talk (Teensy 4.1):** cut the VUSB/VIN trace between the two pads on the underside. After the cut, USB still programs and does serial, it just no longer supplies (or receives) power. Without the cut, plugging USB shorts the buck output to the computer's USB 5V.

## Budget (logic buck)

| Load | Peak budget |
|------|-------------|
| j4_receiver (ESP-NOW TX bursts) | 500 mA |
| j4_stepper_neck (no WiFi) | 250 mA |
| j4_stepper_eyes (no WiFi) | 250 mA |
| j4_talk + Audio Shield | 300 mA |
| 74AHCT125 x2 | ~10 mA |
| **Total** | **~1.3 A** |

A 3 A buck gives comfortable margin. The LED buck and servo buck are sized by their own loads (strip length, servo count and stall behavior), which is exactly why they are separate.

## Wiring notes

- 100-470 uF electrolytic across 5V/GND at each board's feed point; the 1000 uF at the WS2812B injection point is not optional.
- 20-22 AWG is fine for the logic feeds; the servo and LED feeds should be 18 AWG or better depending on run length.
- Star the grounds back to the buck outputs where practical instead of daisy-chaining a thin ground through every board.
- The DM556TE and TMC2209 motor supplies stay exactly as they are; this doc only adds the logic/LED/servo rails beside them.
