#!/usr/bin/env python3
# Johnny 4 system interconnect poster.
#
# One landscape sheet showing all seven boards as blocks, the buses that wire
# them together, and every discrete part in the signal/power path: the WS2812B
# series resistor, the mouth-LED MOSFETs, the buck-feed Schottky, the two
# 3V3->5V level shifters, the three buck converters, and both sets of stepper
# drivers. ESP-NOW is drawn as a radio hop between controller and receiver.
#
# Pure vector via reportlab (no raster, no SVG step). Deliberately plain,
# white-background engineering styling -- flat blocks, thin nets, a legend and
# a schematic title block. No warm/sepia tint anywhere.

import os
from reportlab.lib.pagesizes import letter  # unused ratio ref
from reportlab.pdfgen import canvas
from reportlab.lib import colors

DOCS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(DOCS_DIR, "j4_pin_diagram_poster.pdf")

W, H = 1900.0, 1220.0   # points; ~26.4 x 16.9 in landscape poster

# ---- palette (cool + neutral only; no yellow/sepia) -------------------------
BG        = colors.white
INK       = colors.HexColor("#1b1b1b")
EDGE      = colors.HexColor("#333333")
FAINT     = colors.HexColor("#8a8a8a")
GRID      = colors.HexColor("#e6e6e6")
ESP_HDR   = colors.HexColor("#33475b")   # slate
TEENSY_HDR= colors.HexColor("#3d5a45")   # muted green-slate
PERI_HDR  = colors.HexColor("#5a6470")   # grey-slate
DRV_HDR   = colors.HexColor("#4a4a55")
UART      = colors.HexColor("#0b6bcb")   # blue
I2C       = colors.HexColor("#128a4f")   # green
FIVEV     = colors.HexColor("#cf2e2e")   # red
TWELVEV   = colors.HexColor("#b5179e")   # magenta
MOTORHV   = colors.HexColor("#555555")   # thick grey
RADIO     = colors.HexColor("#6a4bc0")   # violet
COMP      = colors.HexColor("#1b1b1b")

c = canvas.Canvas(OUT, pagesize=(W, H))
c.setTitle("Johnny 4 - system interconnect poster")


# ---- coordinate helpers (work in screen space, y-down) ----------------------
def Y(top):
    return H - top


def box(x, y, w, h, title, sub=None, hdr=ESP_HDR, body=colors.white, r=2):
    """Flat block with a coloured header strip. (x,y) is the top-left."""
    yb = Y(y + h)
    c.setLineWidth(1.1)
    c.setStrokeColor(EDGE)
    c.setFillColor(body)
    c.roundRect(x, yb, w, h, r, stroke=1, fill=1)
    hh = 20
    c.setFillColor(hdr)
    c.roundRect(x, Y(y + hh), w, hh, r, stroke=0, fill=1)
    c.rect(x, Y(y + hh), w, hh - r, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawCentredString(x + w / 2, Y(y + 14.5), title)
    if sub:
        c.setFillColor(INK)
        c.setFont("Helvetica", 7.6)
        ty = y + 32
        for line in sub:
            c.drawString(x + 7, Y(ty), line)
            ty += 10.2
    return {"x": x, "y": y, "w": w, "h": h}


def rP(b, f):  return (b["x"] + b["w"], Y(b["y"] + b["h"] * f))
def lP(b, f):  return (b["x"],          Y(b["y"] + b["h"] * f))
def tP(b, f):  return (b["x"] + b["w"] * f, Y(b["y"]))
def bP(b, f):  return (b["x"] + b["w"] * f, Y(b["y"] + b["h"]))


def wire(pts, color=UART, width=1.6, dash=None):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.setDash(dash or [])
    p = c.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    c.drawPath(p, stroke=1, fill=0)
    c.setDash([])


def dot(x, y, color=INK, r=2.4):
    c.setFillColor(color)
    c.circle(x, y, r, stroke=0, fill=1)


def netlabel(x, y, text, color=INK, size=7.0, anchor="start"):
    c.setFillColor(color)
    c.setFont("Helvetica", size)
    if anchor == "middle":
        c.drawCentredString(x, y, text)
    elif anchor == "end":
        c.drawRightString(x, y, text)
    else:
        c.drawString(x, y, text)


# ---- discrete component symbols (screen coords, y-down) ----------------------
def resistor(cx, cy, label="", horiz=True, color=COMP):
    """Zig-zag resistor centred at (cx,cy)."""
    y0 = Y(cy)
    c.setStrokeColor(color)
    c.setLineWidth(1.4)
    L, amp = 26, 5
    p = c.beginPath()
    if horiz:
        xs = cx - L / 2
        p.moveTo(xs, y0)
        seg = L / 6
        for i in range(1, 6):
            p.lineTo(xs + seg * i, y0 + (amp if i % 2 else -amp))
        p.lineTo(cx + L / 2, y0)
    c.drawPath(p, stroke=1, fill=0)
    if label:
        netlabel(cx, y0 + 9, label, color, 7.2, "middle")


def diode(cx, cy, label="", color=COMP):
    """Schottky diode symbol, current flows left->right."""
    y0 = Y(cy)
    c.setStrokeColor(color); c.setFillColor(color); c.setLineWidth(1.4)
    s = 7
    p = c.beginPath()
    p.moveTo(cx - s, y0 + s); p.lineTo(cx - s, y0 - s); p.lineTo(cx + s, y0)
    p.close()
    c.drawPath(p, stroke=1, fill=1)
    # cathode bar with Schottky S-hooks
    c.line(cx + s, y0 + s, cx + s, y0 - s)
    c.line(cx + s, y0 + s, cx + s + 4, y0 + s)
    c.line(cx + s, y0 - s, cx + s - 4, y0 - s)
    if label:
        netlabel(cx, y0 + 13, label, color, 7.2, "middle")


def mosfet(cx, cy, label="", color=COMP):
    """N-channel MOSFET symbol."""
    y0 = Y(cy)
    c.setStrokeColor(color); c.setFillColor(color); c.setLineWidth(1.3)
    # gate
    c.line(cx - 20, y0, cx - 9, y0)
    c.line(cx - 9, y0 + 9, cx - 9, y0 - 9)
    # channel bar
    c.line(cx - 4, y0 + 9, cx - 4, y0 - 9)
    # drain (up) and source (down)
    c.line(cx - 4, y0 + 6, cx + 12, y0 + 6); c.line(cx + 12, y0 + 6, cx + 12, y0 + 16)
    c.line(cx - 4, y0 - 6, cx + 12, y0 - 6); c.line(cx + 12, y0 - 6, cx + 12, y0 - 16)
    c.line(cx - 4, y0, cx + 12, y0)
    # arrow (n-channel, into channel)
    p = c.beginPath()
    p.moveTo(cx + 1, y0); p.lineTo(cx - 3, y0 + 3); p.lineTo(cx - 3, y0 - 3); p.close()
    c.drawPath(p, stroke=0, fill=1)
    if label:
        netlabel(cx - 4, y0 - 22, label, color, 7.0, "middle")


def radio_icon(cx, cy, label="ESP-NOW", color=RADIO):
    """Concentric transmit arcs on both sides of a node."""
    y0 = Y(cy)
    c.setStrokeColor(color); c.setLineWidth(1.6)
    dot(cx, y0, color, 3)
    for rr in (10, 17, 24):
        c.arc(cx - rr, y0 - rr, cx + rr, y0 + rr, 205, 70)   # left fan
        c.arc(cx - rr, y0 - rr, cx + rr, y0 + rr, -55, 70)   # right fan
    netlabel(cx, y0 + 34, label, color, 8.5, "middle")
    netlabel(cx, y0 - 42, "2.4 GHz LR PHY", FAINT, 7.0, "middle")


def cap(cx, cy, label="", color=COMP):
    """Polarised bulk cap."""
    y0 = Y(cy)
    c.setStrokeColor(color); c.setLineWidth(1.4)
    c.line(cx - 7, y0 + 6, cx + 7, y0 + 6)
    c.arc(cx - 7, y0 - 10, cx + 7, y0 + 2, 20, 140)
    c.line(cx, y0 + 6, cx, y0 + 14)
    c.line(cx, y0 - 10, cx, y0 - 18)
    if label:
        netlabel(cx + 11, y0 - 2, label, color, 7.0, "start")


# =============================================================================
# TITLE
# =============================================================================
c.setFillColor(BG); c.rect(0, 0, W, H, fill=1, stroke=0)
c.setFillColor(INK)
c.setFont("Helvetica-Bold", 24)
c.drawString(40, Y(40), "JOHNNY 4  ·  SYSTEM INTERCONNECT")
c.setFont("Helvetica", 11)
c.setFillColor(FAINT)
c.drawString(42, Y(58), "All seven boards, buses, discrete parts, and power distribution on one sheet. Companion to j4_master_pin_diagram.pdf.")

# thin rule under title
c.setStrokeColor(GRID); c.setLineWidth(1)
c.line(40, Y(70), W - 40, Y(70))

# =============================================================================
# BOARD BLOCKS
# =============================================================================
# ---- operator inputs (far left) ----
jl = box(40, 120, 96, 42, "JOYSTICK L", ["neck L / R"], hdr=PERI_HDR)
jr = box(40, 170, 96, 42, "JOYSTICK R", ["eyes X / Y"], hdr=PERI_HDR)
pots = box(40, 220, 96, 54, "11 POTS", ["brows, nose, lids,", "pivot + 2 faders"], hdr=PERI_HDR)
tog = box(40, 282, 96, 54, "4 TOGGLES", ["laser, vent,", "eyepop, aux"], hdr=PERI_HDR)
kp = box(40, 344, 96, 42, "KEYPADS x2", ["4x4 phrase"], hdr=PERI_HDR)

# ---- controller-side I2C devices ----
adsc = box(168, 150, 170, 120, "ADS1115 x4  (I2C)",
           ["ADS_01 0x48   brows",
            "ADS_02 0x49   joysticks",
            "ADS_03 0x4A   nose/lids",
            "ADS_04 0x4B   pivot/faders"], hdr=PERI_HDR)
pcf = box(168, 286, 170, 40, "PCF8574 x2  0x20/0x21", ["keypad expanders"], hdr=PERI_HDR)

ctrl = box(168, 360, 190, 150, "j4_controller",
           ["TTGO T-Display (ESP32)",
            "I2C  SDA21 / SCL22",
            "Ser1 17/27  -> disp L",
            "Ser2 25/26  -> disp R",
            "toggles 32/33/13/15",
            "ESP-NOW  -> receiver"], hdr=ESP_HDR)

dl = box(52, 560, 168, 92, "j4_display_left",
         ["XIAO ESP32-S3", "ILI9488 portrait", "UART D6/D7 <-> ctrl"], hdr=ESP_HDR)
dr = box(52, 672, 210, 120, "j4_display_right",
         ["XIAO ESP32-S3  (landscape)",
          "own ADS1115 0x48 (5th ADC)",
          "IRIS COLOR BRIGHT VOL pots",
          "streams P: feed -> ctrl Ser2"], hdr=ESP_HDR)

# ---- radio hop ----
radio_icon(520, 250)

# ---- robot hub ----
rcv = box(700, 360, 190, 175, "j4_receiver",
          ["TTGO T-Display (ESP32)",
           "ESP-NOW  <- controller",
           "UART2 2/17  -> j4_talk",
           "UART1 21/22 -> steppers",
           "I2C 32/33   -> PCA9685",
           "GPIO25 -> LED strip",
           "batt sense 34"], hdr=ESP_HDR)

# ---- audio / mouth ----
talk = box(985, 120, 185, 132, "j4_talk",
           ["Teensy 4.1 + Audio Shield",
            "Serial6 24/25 <-> rcv",
            "18 PWM -> mouth LEDs",
            "SGTL5000 -> speaker"], hdr=TEENSY_HDR)
mos = box(1210, 120, 150, 78, "RFP30N06LE x18", ["N-ch MOSFETs", "low-side LED switch"], hdr=DRV_HDR)
mouth = box(1408, 120, 120, 78, "MOUTH LEDs", ["18 ch, 12 V", "anode + resistor"], hdr=PERI_HDR)
spk = box(985, 268, 185, 40, "SPEAKER", ["4-8 ohm via shield"], hdr=PERI_HDR)

# ---- neck steppers ----
neck = box(985, 350, 185, 150, "j4_stepper_neck",
           ["ESP32-D0WD (LOLIN32-Lite)",
            "UART1 4/13  <- receiver",
            "UART2 22/35 -> eyes",
            "STEP/DIR 26/25 33/32 27/14",
            "limits 34/36/39 + 18/19/23"], hdr=ESP_HDR)
buf = box(1210, 350, 150, 66, "SN74AHCT125 x2", ["3.3V -> 5V buffers", "STEP/DIR level shift"], hdr=DRV_HDR)
dm = box(1408, 344, 150, 92, "DM556TE x3", ["stepper drivers", "PUL+/DIR+ (5V)", "20-50 VDC motor"], hdr=DRV_HDR)
neckmot = box(1600, 344, 120, 92, "NECK MOTORS", ["NL / NR / NP", "NEMA23"], hdr=PERI_HDR)
necklim = box(985, 516, 185, 40, "NECK LIMITS", ["6 NC switches, 10k pull-ups"], hdr=PERI_HDR)

# ---- eye steppers ----
eyes = box(985, 585, 185, 120, "j4_stepper_eyes",
           ["ESP32-D0WD (LOLIN32-Lite)",
            "UART1 4/13 <- neck",
            "STEP/DIR 26/25 33/32",
            "TMC UART 17/16"], hdr=ESP_HDR)
tmc = box(1210, 585, 150, 66, "TMC2209 x2", ["stepper drivers", "addr 0b00 / 0b01"], hdr=DRV_HDR)
eyemot = box(1408, 585, 150, 66, "EYE-POP MOTORS", ["EL / ER", "StallGuard home"], hdr=PERI_HDR)
eyelim = box(1408, 665, 150, 40, "EYE LIMITS", ["4 NC, 10k pull-ups"], hdr=PERI_HDR)

# ---- servos + LED strip (column under the receiver) ----
pca = box(700, 555, 190, 66, "PCA9685  0x40", ["16-ch PWM servo driver", "logic 3V3 from receiver"], hdr=DRV_HDR)
servos = box(700, 636, 280, 82, "SERVOS (16 ch)",
             ["3 eyesX/Y+iris   4-11 brows/nose/lids",
              "5 iris(270)      14 LASER   15 VENT",
              "all 50 Hz, powered from servo buck"], hdr=PERI_HDR)
strip = box(700, 733, 210, 60, "WS2812B strip", ["addressable RGB, own 5 V supply"], hdr=PERI_HDR)


# =============================================================================
# SIGNAL NETS
# =============================================================================
# operator inputs -> controller / ADC bank (grey signal stubs)
for b in (jl, jr, pots, tog):
    wire([rP(b, 0.5), (152, rP(b, 0.5)[1]), (adsc["x"], rP(b, 0.5)[1])], FAINT, 1.2)
wire([rP(kp, 0.5), (152, rP(kp, 0.5)[1]), (pcf["x"], rP(kp, 0.5)[1])], FAINT, 1.2)

# ADC + keypad expander -> controller over I2C
wire([bP(adsc, 0.5), (adsc["x"] + adsc["w"] * 0.5, Y(345)), (ctrl["x"] + 20, Y(345)),
      (ctrl["x"] + 20, tP(ctrl, 0.1)[1])], I2C, 1.7)
wire([bP(pcf, 0.7), (pcf["x"] + pcf["w"] * 0.7, tP(ctrl, 0.35)[1])], I2C, 1.7)
netlabel(adsc["x"] + 96, Y(342), "I2C", I2C, 7)

# controller -> displays (UART)
wire([lP(ctrl, 0.75), (150, lP(ctrl, 0.75)[1]), (150, tP(dl, 0.5)[1]), tP(dl, 0.5)], UART, 1.6)
wire([lP(ctrl, 0.9), (140, lP(ctrl, 0.9)[1]), (140, tP(dr, 0.3)[1]), tP(dr, 0.3)], UART, 1.6)

# controller -> radio -> receiver (ESP-NOW dashed)
wire([rP(ctrl, 0.15), (440, rP(ctrl, 0.15)[1]), (440, Y(250)), (496, Y(250))], RADIO, 1.7, [5, 4])
wire([(544, Y(250)), (620, Y(250)), (620, lP(rcv, 0.15)[1]), lP(rcv, 0.15)], RADIO, 1.7, [5, 4])

# receiver -> talk (UART2), routed above the speaker box
wire([tP(rcv, 0.4), (tP(rcv, 0.4)[0], Y(258)), (talk["x"] + 40, Y(258)),
      (talk["x"] + 40, bP(talk, 0.22)[1])], UART, 1.7)
netlabel(tP(rcv, 0.4)[0] + 5, Y(268), "UART2", UART, 7)

# receiver -> neck (UART1)
wire([rP(rcv, 0.55), (935, rP(rcv, 0.55)[1]), (935, lP(neck, 0.3)[1]), lP(neck, 0.3)], UART, 1.7)
netlabel(905, rP(rcv, 0.55)[1] + 4, "UART1", UART, 7)

# neck -> eyes (UART2 down the chain)
wire([bP(neck, 0.2), (bP(neck, 0.2)[0], lP(eyes, 0.2)[1]), lP(eyes, 0.2)], UART, 1.7)

# receiver -> PCA9685 (I2C)
wire([bP(rcv, 0.5), (bP(rcv, 0.5)[0], tP(pca, 0.4)[1])], I2C, 1.7)
netlabel(bP(rcv, 0.5)[0] + 4, tP(pca, 0.4)[1] + 8, "I2C", I2C, 7)

# receiver GPIO25 -> 330R -> WS2812B (down the clear channel left of the column)
yg = lP(rcv, 0.92)[1]
wire([lP(rcv, 0.92), (665, yg), (665, Y(763)), (677, Y(763))], FIVEV, 1.5)
resistor(690, 763, "330", True, COMP)
wire([(703, Y(763)), lP(strip, 0.5)], FIVEV, 1.5)
netlabel(668, yg + 10, "GPIO25 data", FIVEV, 7)

# PCA9685 -> servos fanout
wire([bP(pca, 0.5), (bP(pca, 0.5)[0], tP(servos, 0.5)[1])], MOTORHV, 1.4)

# talk -> MOSFETs -> mouth LEDs
wire([rP(talk, 0.5), lP(mos, 0.5)], FAINT, 1.3)
netlabel(rP(talk, 0.5)[0] + 6, rP(talk, 0.5)[1] + 5, "18x PWM", FAINT, 6.8)
wire([rP(mos, 0.5), lP(mouth, 0.5)], TWELVEV, 1.5)
mosfet(mos["x"] + mos["w"] / 2, 176)      # representative symbol under the label
# talk -> speaker
wire([bP(talk, 0.2), (bP(talk, 0.2)[0], tP(spk, 0.2)[1])], FAINT, 1.3)

# neck STEP/DIR -> buffers -> DM556TE -> motors
wire([rP(neck, 0.55), lP(buf, 0.5)], FAINT, 1.4)
wire([rP(buf, 0.5), lP(dm, 0.5)], FIVEV, 1.5)
netlabel(rP(buf, 0.5)[0] + 4, rP(buf, 0.5)[1] + 5, "5V", FIVEV, 6.8)
wire([rP(dm, 0.5), lP(neckmot, 0.5)], MOTORHV, 2.2)
# neck limits (with a representative 10k pull-up symbol)
wire([bP(neck, 0.6), (bP(neck, 0.6)[0], tP(necklim, 0.5)[1])], FAINT, 1.3)
resistor(necklim["x"] + necklim["w"] - 26, necklim["y"] + 20, "10k x6", True, COMP)

# eyes STEP/DIR -> TMC2209 -> motors
wire([rP(eyes, 0.5), lP(tmc, 0.5)], FAINT, 1.4)
wire([rP(tmc, 0.5), lP(eyemot, 0.5)], MOTORHV, 2.2)
wire([bP(eyemot, 0.5), (bP(eyemot, 0.5)[0], tP(eyelim, 0.5)[1])], FAINT, 1.2)
resistor(eyelim["x"] + eyelim["w"] - 26, eyelim["y"] + 20, "10k x4", True, COMP)


# =============================================================================
# POWER BAND
# =============================================================================
PBY = 840
c.setStrokeColor(GRID); c.setLineWidth(1)
c.line(40, Y(PBY - 12), W - 40, Y(PBY - 12))
c.setFillColor(INK); c.setFont("Helvetica-Bold", 12)
c.drawString(40, Y(PBY + 4), "POWER DISTRIBUTION")
c.setFillColor(FAINT); c.setFont("Helvetica", 8)
c.drawString(200, Y(PBY + 3), "all grounds common  ·  bulk cap at every feed  ·  see POWER.md")

batt = box(40, PBY + 20, 120, 96, "BATTERY", ["main pack", "-> rails below"], hdr=DRV_HDR)

b1 = box(300, PBY + 20, 150, 56, "BUCK 5V / 3A", ["logic rail"], hdr=DRV_HDR)
b2 = box(300, PBY + 90, 150, 40, "BUCK 5V", ["LED rail"], hdr=DRV_HDR)
b3 = box(300, PBY + 140, 150, 40, "BUCK 5-6V", ["servo rail"], hdr=DRV_HDR)

# battery -> bucks + HV/12V rails
wire([rP(batt, 0.3), (250, rP(batt, 0.3)[1]), (250, lP(b1, 0.5)[1]), lP(b1, 0.5)], INK, 1.5)
wire([(250, lP(b1, 0.5)[1]), (250, lP(b2, 0.5)[1]), lP(b2, 0.5)], INK, 1.5)
wire([(250, lP(b2, 0.5)[1]), (250, lP(b3, 0.5)[1]), lP(b3, 0.5)], INK, 1.5)
dot(250, lP(b1, 0.5)[1]); dot(250, lP(b2, 0.5)[1])

# motor HV rail + 12V rail as labelled horizontal buses high in the band
railHV = Y(PBY + 30)
railV12 = Y(PBY + 62)
wire([rP(batt, 0.7), (500, rP(batt, 0.7)[1]), (500, railHV), (1740, railHV)], MOTORHV, 2.4)
netlabel(1745, railHV - 3, "MOTOR HV", MOTORHV, 8)
wire([(520, rP(batt, 0.85)[1]), (520, railV12), (1360, railV12)], TWELVEV, 1.8)
netlabel(1365, railV12 - 3, "12 V", TWELVEV, 8)

# Schottky on logic buck output
dpx = b1["x"] + b1["w"] + 26
diode(dpx, PBY + 48, "SS34")
wire([rP(b1, 0.5), (dpx - 11, rP(b1, 0.5)[1])], FIVEV, 1.8)
five_bus_y = rP(b1, 0.5)[1]
wire([(dpx + 11, five_bus_y), (1740, five_bus_y)], FIVEV, 1.8)
netlabel(1745, five_bus_y - 3, "5 V logic", FIVEV, 8)

# 5V logic taps (dotted risers off the bus, labelled), spread along the rail
def riser(x, label):
    wire([(x, five_bus_y), (x, five_bus_y + 24)], FIVEV, 1.2, [2, 3])
    netlabel(x, five_bus_y + 32, label, FIVEV, 6.8, "middle")
    dot(x, five_bus_y, FIVEV, 2)

for x, lbl in [(760, "rcv 5V"), (1010, "neck USB"), (1230, "eyes USB"),
               (1450, "74AHCT125 VCC"), (1660, "Teensy VIN")]:
    riser(x, lbl)

# LED buck -> WS2812B strip (own 5 V, 1000uF at the injection point)
wire([rP(b2, 0.5), (600, rP(b2, 0.5)[1]), (600, bP(strip, 0.4)[1])], FIVEV, 1.6)
cap(600, PBY + 60, "1000uF")
netlabel(568, Y(PBY + 30), "5 V LED", FIVEV, 7, "end")

# servo buck -> PCA9685 V+
wire([rP(b3, 0.5), (566, rP(b3, 0.5)[1]), (566, bP(pca, 0.7)[1]), bP(pca, 0.7)], FIVEV, 1.6)
netlabel(552, Y(PBY + 4), "5-6 V servo", FIVEV, 7, "end")

# HV rail drops to the stepper drivers
for x in (dm["x"] + dm["w"] * 0.5, tmc["x"] + tmc["w"] * 0.5):
    wire([(x, railHV), (x, railHV + 20)], MOTORHV, 1.2, [2, 3])
    dot(x, railHV, MOTORHV, 2)
# 12V rail drop to MOSFET/mouth LEDs
xv = mos["x"] + mos["w"] * 0.5
wire([(xv, railV12), (xv, railV12 + 20)], TWELVEV, 1.2, [2, 3])
dot(xv, railV12, TWELVEV, 2)


# =============================================================================
# TITLE BLOCK + LEGEND  (top-right corner, clear of the MOUTH LEDs block)
# =============================================================================
def trect(x, top, w, h, sw=1.0):
    c.setStrokeColor(EDGE); c.setLineWidth(sw); c.setFillColor(colors.white)
    c.rect(x, Y(top + h), w, h, stroke=1, fill=1)

# schematic title block
tbx, tby, tbw, tbh = 1560, 88, 300, 70
trect(tbx, tby, tbw, tbh, 1.2)
c.line(tbx, Y(tby + 26), tbx + tbw, Y(tby + 26))
c.line(tbx + tbw * 0.60, Y(tby), tbx + tbw * 0.60, Y(tby + tbh))
c.setFillColor(INK); c.setFont("Helvetica-Bold", 10.5)
c.drawString(tbx + 10, Y(tby + 17), "Johnny 4 - System Interconnect")
c.setFont("Helvetica", 7.3); c.setFillColor(FAINT)
c.drawString(tbx + 10, Y(tby + 40), "Project:  Johnny 4")
c.drawString(tbx + 10, Y(tby + 52), "Drawn:    K. Lange")
c.drawString(tbx + 10, Y(tby + 64), "Repo:     johnny_4_docs")
c.setFillColor(INK); c.setFont("Helvetica", 7.3)
c.drawString(tbx + tbw * 0.60 + 8, Y(tby + 40), "Rev:   B")
c.drawString(tbx + tbw * 0.60 + 8, Y(tby + 52), "Date:  2026-07-12")
c.drawString(tbx + tbw * 0.60 + 8, Y(tby + 64), "Sheet: 1/1")

# legend, below the title block
lx, ly, lw, lh = 1560, 172, 300, 130
trect(lx, ly, lw, lh)
c.setFillColor(INK); c.setFont("Helvetica-Bold", 9)
c.drawString(lx + 10, Y(ly + 15), "LEGEND")
items = [
    (UART, "UART serial link"),
    (I2C, "I2C bus"),
    (RADIO, "ESP-NOW radio (2.4 GHz)"),
    (FIVEV, "5 V rail / data"),
    (TWELVEV, "12 V rail"),
    (MOTORHV, "motor high-voltage rail"),
]
yy = ly + 30
for col, txt in items:
    c.setStrokeColor(col); c.setLineWidth(2.2)
    c.setDash([4, 3] if col == RADIO else [])
    c.line(lx + 12, Y(yy), lx + 44, Y(yy))
    c.setDash([])
    c.setFillColor(INK); c.setFont("Helvetica", 7.8)
    c.drawString(lx + 52, Y(yy + 2.6), txt)
    yy += 13.5
c.setFillColor(FAINT); c.setFont("Helvetica-Oblique", 7)
c.drawString(lx + 10, Y(ly + 122), "Grey stubs = analog / GPIO.  Pin-exact detail in the master PDF.")

c.showPage()
c.save()
print("wrote", OUT)
