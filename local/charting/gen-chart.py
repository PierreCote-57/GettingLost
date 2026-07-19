#!/usr/bin/env python3
"""Cabin climate chart — pure-Python SVG generator (no Chart.js, no CDN, no
headless Chrome, no Pillow). Reads the TempU03 CSV logger and writes one SVG.
Pierre converts the SVG -> PNG in IntelliJ (~1 s) for the howto-climate gallery.

Dual-axis: Temperature (left, red) + Humidity (right, blue), 900x520.

Usage:  python3 gen-chart.py <csv> [eva:1|2] [--win HH:MM-HH:MM] [--xstep HOURS]
  <csv>     logger CSV; LOCATION is inferred from its filename prefix
            (cabin-indoor | cabin-outdoor | fridge | freezer). Fails loudly otherwise.
  [eva]     1|2 -> Single|Double Eva-dry; REQUIRED for cabin-indoor, ignored elsewhere.
  --win     X-axis window as START-END clock times, e.g. 18:00-06:00. Anchored to the
            first data date; end <= start rolls to the next day (overnight). Overrides
            the in-source WIN_START/WIN_END. Omit -> data range snapped to 12h ticks.
  --xstep   hours between X-axis ticks (e.g. 1 or 2). Omit -> auto by span (12/2/1h).
Claude asks the Eva-dry count once per CSV per session (clickable) and passes it here.

Per-location axis bands + thermostat live in BANDS below. Temp & humidity both
span 4 intervals so their gridlines coincide. All values clamp to their band; the
10-min cadence is dense enough that no band-edge interpolation is needed.

X axis default = data range snapped out to the enclosing 12h ticks. Focus one chart
by setting WIN_START/WIN_END; weekday ticks come from the real dates.

Title:    cabin-indoor/outdoor -> "Cabin climate (<Location>)"; fridge/freezer -> "<Location>".
Subtitle: cabin-indoor -> "<Single|Double> Eva-dry, <date range>"; else "<date range>".
Output:   <same base>.svg written beside the CSV. Only the CSV persists — the svg (and
          the PNG Pierre makes from it) are deleted after the PNG is uploaded to WP.
"""
import argparse, csv, datetime, math, os, sys

# ---------- window (optional per-chart tweak) ----------
# None,None = full data range (default). The --win CLI flag overrides these per run;
# set them here only for a hard-coded default. e.g.
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
    "Outdoors":       dict(temp=(10, 30, 5),  hum=(30, 70, 10), thermostat=None, thermostat_f=70),
    "Fridge":         dict(temp=(0, 20, 5),   hum=(30, 70, 10), thermostat=None),
    "Freezer":        dict(temp=(-20, 0, 5),  hum=(30, 70, 10), thermostat=None),
}

# ---------- config ----------
# location + dehumidifier are filled from the CLI (see bottom); brand is the title base.
CFG = dict(brand="Cabin climate")

# CSV filename prefix -> location. Location is inferred from the name, not asked.
PREFIX_TO_LOCATION = {
    "cabin-indoor":  "Indoor Storage",
    "cabin-outdoor": "Outdoors",
    "fridge":        "Fridge",
    "freezer":       "Freezer",
}

# ---------- geometry ----------
W, H = 900, 520
PL, PR, PT, PB = 62, 838, 64, 482          # plot box edges (symmetric margins for 2 axes)
PW, PH = PR-PL, PB-PT
FONT = "Helvetica, Arial, sans-serif"
INK, GRID, GREY, GREEN = "#000000", "#e1e0d9", "#6b6b6b", "#1a9850"

def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def build_svg(times, series, cfg, anchor):
    L, R = cfg["left"], cfg["right"]
    # Axis range: honor an explicit WIN_START/WIN_END exactly; otherwise snap the
    # data range out to the enclosing 12h ticks.
    wmin = (WIN_START - anchor).total_seconds() / 3600 if WIN_START else math.floor(times[0]  / 12) * 12
    wmax = (WIN_END   - anchor).total_seconds() / 3600 if WIN_END   else math.ceil (times[-1] / 12) * 12
    span = wmax - wmin
    # tick spacing: explicit --xstep wins, else auto (finer ticks for short windows).
    tstep = cfg["xstep"] if cfg.get("xstep") else (12 if span >= 24 else (2 if span > 8 else 1))
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
    def fmt_clock(h):
        m = int(round(h * 60)) % 1440
        return "%02d:%02d" % (m // 60, m % 60)
    t = wmin
    while t <= wmax + 1e-9:
        x = X(t)
        p.append('<line x1="%.2f" y1="%.1f" x2="%.2f" y2="%.1f" stroke="%s"/>' % (x, PT, x, PB, GRID))
        p.append('<text x="%.2f" y="%.1f" text-anchor="middle" font-size="14" fill="%s">%s</text>' % (x, PB+18, INK, fmt_clock(t)))
        if t % 24 == 0:
            day = (anchor + datetime.timedelta(hours=t)).strftime("%a")
            p.append('<text x="%.2f" y="%.1f" text-anchor="middle" font-size="14" fill="%s">%s</text>' % (x, PB+35, INK, day))
        t += tstep

    # axis borders: left, right, bottom
    for xb in (PL, PR):
        p.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s"/>' % (xb, PT, xb, PB, INK))
    p.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s"/>' % (PL, PB, PR, PB, INK))

    # data lines (clamped to band via scaleY)
    for ax, Y in ((L, YL), (R, YR)):
        pts = " ".join("%.2f,%.2f" % (X(t), Y(v)) for t, v in zip(times, series[ax["src"]]))
        p.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="3" '
                 'stroke-linejoin="round" stroke-linecap="round"/>' % (pts, ax["color"]))

    # thermostat setpoint — solid bold green reference line on the temperature axis.
    # thermostat_f (°F) takes priority; positioned via °C conversion, labeled °F.
    ts, tf = cfg.get("thermostat"), cfg.get("thermostat_f")
    if tf is not None:
        ty, label = YL((tf - 32) * 5 / 9), "Thermostat %d °F" % tf
    elif ts is not None:
        ty, label = YL(ts), "Thermostat %d °C" % ts
    else:
        ty = None
    if ty is not None:
        p.append('<line x1="%d" y1="%.2f" x2="%d" y2="%.2f" stroke="%s" stroke-width="3.5"/>' % (PL, ty, PR, ty, GREEN))
        p.append('<text x="%d" y="%.2f" text-anchor="end" font-size="14" fill="%s">%s</text>' % (PR-6, ty-5, GREEN, label))

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

# ---- CLI: python3 gen-chart.py <csv> [eva:1|2] [--win HH:MM-HH:MM] [--xstep HOURS] ----
ap = argparse.ArgumentParser(usage="gen-chart.py <csv> [eva:1|2] [--win HH:MM-HH:MM] [--xstep HOURS]")
ap.add_argument("csv", help="logger CSV; location inferred from filename prefix")
ap.add_argument("eva", nargs="?", choices=["1", "2"], help="Eva-dry count (required for cabin-indoor)")
ap.add_argument("--win", metavar="START-END", help="X-axis window, e.g. 18:00-06:00 (end <= start rolls next day)")
ap.add_argument("--xstep", type=float, metavar="HOURS", help="hours between X-axis ticks (default: auto by span)")
ap.add_argument("--title", metavar="TEXT", help="override the chart title, e.g. 'Freezer (Level 3)'")
args = ap.parse_args()
SRC = args.csv

stem = os.path.splitext(os.path.basename(SRC))[0]
CFG["location"] = next((loc for pre, loc in PREFIX_TO_LOCATION.items() if stem.startswith(pre)), None)
if CFG["location"] is None:
    sys.exit("gen-chart.py: can't infer location from '%s' — name it one of %s + '-<date>.csv'"
             % (os.path.basename(SRC), " | ".join(PREFIX_TO_LOCATION)))

if CFG["location"] == "Indoor Storage":
    if args.eva is None:
        sys.exit("gen-chart.py: Indoor Storage needs the Eva-dry count — pass 1 or 2")
    CFG["dehumidifier"] = "Single Eva-dry" if args.eva == "1" else "Double Eva-dry"

# --win overrides the in-source WIN_START/WIN_END, anchored to the data.
if args.win:
    try:
        s_str, e_str = args.win.split("-")
        s_h, s_m = [int(x) for x in s_str.strip().split(":")]
        e_h, e_m = [int(x) for x in e_str.strip().split(":")]
    except ValueError:
        sys.exit("gen-chart.py: --win must look like 18:00-06:00")
    peek = load(SRC)                                # unfiltered peek to place the window
    fd = peek[3]                                    # first data date
    first_dt = peek[5] + datetime.timedelta(hours=peek[0][0])   # first data timestamp
    WIN_START = datetime.datetime(fd.year, fd.month, fd.day, s_h, s_m)
    WIN_END   = datetime.datetime(fd.year, fd.month, fd.day, e_h, e_m)
    if WIN_END <= WIN_START:                        # overnight window rolls to the next day
        WIN_END += datetime.timedelta(days=1)
    while WIN_END < first_dt:                        # window sits before the data — roll forward
        WIN_START += datetime.timedelta(days=1)
        WIN_END   += datetime.timedelta(days=1)

CFG["xstep"] = args.xstep

times, temps, hums, d0, d1, anchor = load(SRC, WIN_START, WIN_END)

# per-location axis bands + thermostat
b = BANDS[CFG["location"]]
CFG["left"]  = dict(title="Temperature (°C)", lo=b["temp"][0], hi=b["temp"][1], step=b["temp"][2], suffix="°", color="#d62728", src="temp")
CFG["right"] = dict(title="Humidity (%RH)",   lo=b["hum"][0],  hi=b["hum"][1],  step=b["hum"][2],  suffix="%", color="#2166c4", src="hum")
CFG["thermostat"] = b["thermostat"]
CFG["thermostat_f"] = b.get("thermostat_f")

# title + subtitle
if CFG["location"] in ("Fridge", "Freezer"):
    CFG["title"] = CFG["location"]                       # equipment: the location name IS the title
else:
    CFG["title"] = "%s (%s)" % (CFG["brand"], CFG["location"])
if args.title:
    CFG["title"] = args.title                            # per-run override (e.g. thermostat level)
if CFG["location"] == "Indoor Storage":
    CFG["subtitle"] = "%s, %s" % (CFG["dehumidifier"], date_range(d0, d1))
else:
    CFG["subtitle"] = date_range(d0, d1)

svg = build_svg(times, {"temp": temps, "hum": hums}, CFG, anchor)

# Output: SVG beside the CSV, same base name (cabin-indoor-2026-07-13.csv -> .svg).
OUT = os.path.splitext(SRC)[0] + ".svg"
with open(OUT, "w") as f: f.write(svg)
print("points:", len(times), "range:", d0, "->", d1, "-> wrote", OUT)
