#!/usr/bin/env python3
"""Cabin climate chart — pure-Python SVG generator (no Chart.js, no CDN, no
headless Chrome, no Pillow). Reads the TempU03 CSV logger and writes one SVG.
Pierre converts the SVG -> PNG in IntelliJ (~1 s) for the howto-climate gallery.

Dual-axis: Temperature (left, red) + Humidity (right, blue), 900x520.

BEFORE each generation, Claude asks Pierre (clickable AskUserQuestion), then sets
CFG["location"] / CFG["dehumidifier"] from the answers:
  1. Location?  ->  Indoor Storage | Outdoors | Fridge | Freezer
  2. How many Eva-dry?  (1 -> "Single Eva-dry", 2 -> "Double Eva-dry")
     — ASKED ONLY when Location == Indoor Storage.

Per-location axis bands + thermostat live in BANDS below. Temp & humidity both
span 4 intervals so their gridlines coincide. All values clamp to their band; the
10-min cadence is dense enough that no band-edge interpolation is needed.

X axis = the data's own range (WIN_START/WIN_END = None). To focus one chart on a
sub-range, set those two datetimes; day-name ticks come from the real weekdays.

Title rules:   Indoor Storage / Outdoors  ->  "Cabin climate (<Location>)"
               Fridge / Freezer           ->  just "<Location>"
Subtitle:      Indoor Storage  ->  "<Single|Double> Eva-dry, <date range>"
               everything else ->  "<date range>"   (range derived from the data)
Filename:      "<base>-<startdate>.svg", lowercase, ISO start date.
"""
import csv, datetime, math

# ---------- data ----------
SRC = "/Users/pierrecote/src/github/GettingLost/local/charting/cabin-indoor-2026-07-13.csv"
# Date/time window — None,None = the full data range (default). Tweak per chart, e.g.
#   WIN_START = datetime.datetime(2026, 7, 13, 5, 0)
#   WIN_END   = datetime.datetime(2026, 7, 17, 12, 0)
WIN_START = None
WIN_END   = None

def load(src, win_start=None, win_end=None):
    """Read all rows within the window; times = decimal hours from the first
    included point's midnight. Returns times, temps, hums, first/last date, anchor."""
    pts = []
    started = False
    with open(src, newline="") as f:
        for row in csv.reader(f):
            if not row: continue
            if row[0].strip() == "Date": started = True; continue
            if not started or row[0].strip().startswith("*"): continue
            try:
                d = datetime.datetime.strptime(row[0].strip(), "%m/%d/%Y").date()
            except ValueError:
                continue
            hh, mm, ss = [int(x) for x in row[1].strip().split(":")]
            dt = datetime.datetime(d.year, d.month, d.day, hh, mm, ss)
            if win_start and dt < win_start: continue
            if win_end and dt > win_end: continue
            pts.append((dt, float(row[2].strip()), float(row[3].strip())))
    anchor = datetime.datetime.combine(pts[0][0].date(), datetime.time())
    times = [(dt - anchor).total_seconds() / 3600 for dt, _, _ in pts]
    temps = [t for _, t, _ in pts]
    hums  = [h for _, _, h in pts]
    return times, temps, hums, pts[0][0].date(), pts[-1][0].date(), anchor

def date_range(d0, d1):
    """Human range from the data: 'July 13-17, 2026', etc."""
    if d0 == d1:
        return d0.strftime("%B %-d, %Y")
    if (d0.year, d0.month) == (d1.year, d1.month):
        return "%s %d-%d, %d" % (d0.strftime("%B"), d0.day, d1.day, d0.year)
    if d0.year == d1.year:
        return "%s - %s, %d" % (d0.strftime("%B %-d"), d1.strftime("%B %-d"), d0.year)
    return "%s - %s" % (d0.strftime("%b %-d, %Y"), d1.strftime("%b %-d, %Y"))

# ---------- per-location bands ----------
# temp (lo, hi, step) | hum (lo, hi, step) | thermostat °C (None = no line).
# Temp span 20 (step 5) and hum span 40 (step 10) both give 4 intervals -> gridlines coincide.
BANDS = {
    "Indoor Storage": dict(temp=(0, 20, 5),   hum=(20, 60, 10), thermostat=6),
    "Outdoors":       dict(temp=(10, 30, 5),  hum=(30, 70, 10), thermostat=20),
    "Fridge":         dict(temp=(0, 20, 5),   hum=(30, 70, 10), thermostat=None),
    "Freezer":        dict(temp=(-20, 0, 5),  hum=(30, 70, 10), thermostat=None),
}

# ---------- config ----------
CFG = dict(
    brand="Cabin climate",          # title base; the Location fills the (parenthetical)
    location="Indoor Storage",      # set from the Location question
    dehumidifier="Single Eva-dry",  # set from the Eva-dry question; only used for Indoor Storage
)

# ---------- geometry ----------
W, H = 900, 520
PL, PR, PT, PB = 62, 838, 64, 482          # plot box edges (symmetric margins for 2 axes)
PW, PH = PR-PL, PB-PT
FONT = "Helvetica, Arial, sans-serif"
INK, GRID, GREY, GREEN = "#000000", "#e1e0d9", "#6b6b6b", "#1a9850"

def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def build_svg(times, series, cfg, anchor):
    L, R = cfg["left"], cfg["right"]
    wmin = math.floor(times[0]  / 12) * 12      # tick at/left of the first point
    wmax = math.ceil (times[-1] / 12) * 12      # tick at/right of the last point
    def X(t): return PL + (t - wmin) / (wmax - wmin) * PW
    def scaleY(ax):
        lo, hi = ax["lo"], ax["hi"]
        return lambda v: PB - (max(lo, min(hi, v)) - lo) / (hi - lo) * PH
    YL, YR = scaleY(L), scaleY(R)
    cy = (PT + PB) / 2
    nticks = (L["hi"] - L["lo"]) // L["step"]   # shared interval count (L & R aligned)

    p = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
         'viewBox="0 0 %d %d" font-family="%s">' % (W, H, W, H, FONT)]
    p.append('<rect width="%d" height="%d" fill="#fff"/>' % (W, H))

    # shared horizontal gridlines, with left + right value labels
    for i in range(nticks + 1):
        vl = L["lo"] + L["step"] * i
        vr = R["lo"] + R["step"] * i
        y = YL(vl)
        p.append('<line x1="%.1f" y1="%.2f" x2="%.1f" y2="%.2f" stroke="%s"/>' % (PL, y, PR, y, GRID))
        p.append('<text x="%.1f" y="%.2f" text-anchor="end" dominant-baseline="middle" '
                 'font-size="14" fill="%s">%d%s</text>' % (PL-8, y, INK, vl, L["suffix"]))
        p.append('<text x="%.1f" y="%.2f" text-anchor="start" dominant-baseline="middle" '
                 'font-size="14" fill="%s">%d%s</text>' % (PR+8, y, INK, vr, R["suffix"]))

    # vertical gridlines every 12h; 24h time + real weekday name at midnight
    def fmt_clock(h): return "%02d:00" % (int(round(h)) % 24)
    t = wmin                                     # edges are already on 12h ticks
    while t <= wmax:
        x = X(t)
        p.append('<line x1="%.2f" y1="%.1f" x2="%.2f" y2="%.1f" stroke="%s"/>' % (x, PT, x, PB, GRID))
        p.append('<text x="%.2f" y="%.1f" text-anchor="middle" font-size="14" fill="%s">%s</text>' % (x, PB+18, INK, fmt_clock(t)))
        if t % 24 == 0:
            day = (anchor + datetime.timedelta(hours=t)).strftime("%a")
            p.append('<text x="%.2f" y="%.1f" text-anchor="middle" font-size="14" fill="%s">%s</text>' % (x, PB+35, INK, day))
        t += 12

    # axis borders: left, right, bottom
    for xb in (PL, PR):
        p.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s"/>' % (xb, PT, xb, PB, INK))
    p.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s"/>' % (PL, PB, PR, PB, INK))

    # data lines (clamped to band via scaleY)
    for ax, Y in ((L, YL), (R, YR)):
        pts = " ".join("%.2f,%.2f" % (X(t), Y(v)) for t, v in zip(times, series[ax["src"]]))
        p.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="3" '
                 'stroke-linejoin="round" stroke-linecap="round"/>' % (pts, ax["color"]))

    # thermostat setpoint — solid bold green reference line on the temperature axis
    ts = cfg.get("thermostat")
    if ts is not None:
        ty = YL(ts)
        p.append('<line x1="%d" y1="%.2f" x2="%d" y2="%.2f" stroke="%s" stroke-width="3.5"/>' % (PL, ty, PR, ty, GREEN))
        p.append('<text x="%d" y="%.2f" text-anchor="end" font-size="14" fill="%s">Thermostat %d °C</text>' % (PR-6, ty-5, GREEN, ts))

    # title + subtitle
    p.append('<text x="%d" y="30" text-anchor="middle" font-size="24" font-weight="bold" fill="%s">%s</text>' % (W//2, INK, esc(cfg["title"])))
    p.append('<text x="%d" y="52" text-anchor="middle" font-size="18" fill="%s">%s</text>' % (W//2, GREY, esc(cfg["subtitle"])))
    # axis titles, 18pt, colored to match their line
    p.append('<text x="18" y="%.1f" transform="rotate(-90 18 %.1f)" text-anchor="middle" font-size="18" fill="%s">%s</text>' % (cy, cy, L["color"], esc(L["title"])))
    rx = W - 18
    p.append('<text x="%d" y="%.1f" transform="rotate(90 %d %.1f)" text-anchor="middle" font-size="18" fill="%s">%s</text>' % (rx, cy, rx, cy, R["color"], esc(R["title"])))

    # legend (top-right, inside the plot's empty upper corner)
    lx, ly = PR - 150, PT + 18
    for label, color in (("Temperature", L["color"]), ("Humidity", R["color"])):
        p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="3"/>' % (lx, ly, lx+22, ly, color))
        p.append('<text x="%.1f" y="%.1f" dominant-baseline="middle" font-size="13" fill="%s">%s</text>' % (lx+28, ly, INK, label))
        ly += 20

    p.append('</svg>')
    return "\n".join(p)

times, temps, hums, d0, d1, anchor = load(SRC, WIN_START, WIN_END)

# per-location axis bands + thermostat
b = BANDS[CFG["location"]]
CFG["left"]  = dict(title="Temperature (°C)", lo=b["temp"][0], hi=b["temp"][1], step=b["temp"][2], suffix="°", color="#d62728", src="temp")
CFG["right"] = dict(title="Humidity (%RH)",   lo=b["hum"][0],  hi=b["hum"][1],  step=b["hum"][2],  suffix="%", color="#2166c4", src="hum")
CFG["thermostat"] = b["thermostat"]

# title + subtitle
if CFG["location"] in ("Fridge", "Freezer"):
    CFG["title"] = CFG["location"]                       # equipment: the location name IS the title
else:
    CFG["title"] = "%s (%s)" % (CFG["brand"], CFG["location"])
if CFG["location"] == "Indoor Storage":
    CFG["subtitle"] = "%s, %s" % (CFG["dehumidifier"], date_range(d0, d1))
else:
    CFG["subtitle"] = date_range(d0, d1)

svg = build_svg(times, {"temp": temps, "hum": hums}, CFG, anchor)

# Filename: lowercase location base + start date (ISO). One Eva-dry config per
# start date, so the count is not encoded. Pierre renames IntelliJ's ".svg.png"
# to "<base>-<date>.png" for the gallery.
BASE = {"Indoor Storage": "cabin-indoor", "Outdoors": "cabin-outdoor",
        "Fridge": "fridge", "Freezer": "freezer"}
fname = "%s-%s.svg" % (BASE[CFG["location"]], d0.strftime("%Y-%m-%d"))
OUT = "/Users/pierrecote/src/github/GettingLost/local/charting/" + fname
with open(OUT, "w") as f: f.write(svg)
print("points:", len(times), "range:", d0, "->", d1, "-> wrote", OUT)
