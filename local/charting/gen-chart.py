#!/usr/bin/env python3
"""Cabin climate chart — pure-Python SVG generator (no Chart.js, no CDN, no
headless Chrome, no Pillow). Reads TempU03 logger CSVs and writes one SVG.
Pierre converts the SVG -> PNG in IntelliJ (~1 s) for the howto-climate gallery.

Two modes:
  single   Temperature (left, red) + Humidity (right, blue), dual axis, 900x520.
  overlay  One measure, N nights of the same clock window superimposed, one colour
           per night (NIGHT_COLORS) with a matching legend. Right axis dropped.
           --overlay switches this on.

Usage:
  gen-chart.py --csv FILE [FILE ...] [--scale NAME] [--eva 1|2]
               [--thermostat [N]C|F] [--win HH:MM-HH:MM] [--days N]
               [--overlay DATES|all] [--measure temp|hum|both]
               [--xstep HOURS] [--title TEXT]

  --csv         one or more logger CSVs. In single mode the first is used; in
                overlay mode every night is taken from whichever file covers it.
                SCALE is inferred from the filename prefix (cabin-indoor |
                cabin-outdoor | fridge | freezer) unless --scale is given.
  --scale       axis band to draw against: Indoor Storage | Outdoors | Fridge |
                Freezer. Overrides the filename inference; see BANDS below.
  --eva         1|2 -> Single|Double Eva-dry; REQUIRED for Indoor Storage, ignored
                elsewhere. Claude asks once per CSV per session and passes it here.
  --thermostat  setpoint as [digits] + C|F: "3C", "70F", "-10C". The unit also sets
                the temperature axis unit, so a 70F setpoint draws a 70F scale. The
                bare unit ("C" / "F") selects the scale unit and draws NO setpoint
                line. Omit entirely -> the band's own setpoint on a Celsius scale.
  --win         X-axis window as START-END clock times, e.g. 22:00-08:00. Anchored to
                the first data date; end <= start rolls to the next day (overnight).
                Overrides the in-source WIN_START/WIN_END. Omit -> data range snapped
                to 12h ticks. REQUIRED with --overlay.
  --days        how many days the window spans, for periods longer than one day. A
                storage week is --win 13:00-13:00 --days 4 (Mon 1PM -> Fri 1PM).
  --overlay     comma-separated period start dates (7/18,7/19 or 2026-07-18), or "all"
                for every period in the CSVs with full coverage of --win. Each period is
                re-anchored to the window start so the lines superimpose. Weekday tick
                labels appear when every period starts on the same weekday.
  --measure     which series the overlay draws: temp (default), hum, or both. temp/hum
                draw one line per period from NIGHT_COLORS. both restores the dual axis
                and keeps red=temperature / blue=humidity, telling the periods apart by
                dash pattern (DASHES) instead — readable to about three periods.
  --xstep       hours between X-axis ticks (e.g. 1 or 2). Omit -> auto by span (12/2/1h).
  --title       override the chart title, e.g. 'Freezer (Level 3)'.

Per-scale axis bands + setpoint live in BANDS below, in Celsius. Temp & humidity both
span 4 intervals so their gridlines coincide; the Fahrenheit band is DERIVED to keep
that invariant (convert, snap lo down to a multiple of 5, smallest step from 5/10/20
whose 4 intervals cover the span). All values clamp to their band; the 10-min cadence
is dense enough that no band-edge interpolation is needed.

X axis default = data range snapped out to the enclosing 12h ticks. Focus one chart
by setting WIN_START/WIN_END; weekday ticks come from the real dates (single mode only
— in overlay the nights differ, so weekday labels are suppressed).

Title:    Indoor Storage/Outdoors -> "Cabin climate (<Scale>)"; Fridge/Freezer -> "<Scale>".
Subtitle: Indoor Storage -> "<Single|Double> Eva-dry, <date range>"; overlay -> "<N>
          nights, <date range>" (the legend names each one); else "<date range>".
Output:   single  -> <same base>.svg beside the CSV.
          overlay -> the scale's slug beside the first CSV: cabin-outdoors.svg,
                     cabin-indoor-storage.svg, fridge.svg, freezer.svg.
          Only the CSV persists — the svg (and the PNG Pierre makes from it) are
          deleted after the PNG is uploaded to WP.
"""
import argparse, csv, datetime, math, os, re, sys

# ---------- window (optional per-chart tweak) ----------
# None,None = full data range (default). The --win CLI flag overrides these per run;
# set them here only for a hard-coded default. e.g.
#   WIN_START = datetime.datetime(2026, 7, 13, 5, 0)
#   WIN_END   = datetime.datetime(2026, 7, 17, 12, 0)
WIN_START = None
WIN_END   = None

def read_pts(src):
    """Every (datetime, tempC, hum%) row in a TempU03 CSV, in file order."""
    pts, started = [], False
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
            pts.append((datetime.datetime(d.year, d.month, d.day, hh, mm, ss),
                        float(row[2].strip()), float(row[3].strip())))
    return pts

def load(src, win_start=None, win_end=None):
    """Read all rows within the window; times = decimal hours from the first
    included point's midnight. Returns times, temps, hums, first/last date, anchor."""
    pts = [p for p in read_pts(src)
           if not (win_start and p[0] < win_start) and not (win_end and p[0] > win_end)]
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

# ---------- per-scale bands (Celsius) ----------
# temp (lo, hi, step) | hum (lo, hi, step) | setpoint °C (None = no line).
# Temp span 20 (step 5) and hum span 40 (step 10) both give 4 intervals -> gridlines coincide.
BANDS = {
    "Indoor Storage": dict(temp=(0, 40, 10),  hum=(20, 60, 10), thermostat=6,
                           temp_f=(20, 100, 20)),
    "Outdoors":       dict(temp=(10, 30, 5),  hum=(30, 70, 10), thermostat=None, thermostat_f=70),
    "Fridge":         dict(temp=(0, 20, 5),   hum=(30, 70, 10), thermostat=None),
    "Freezer":        dict(temp=(-20, 0, 5),  hum=(30, 70, 10), thermostat=None),
}

def to_f(c): return c * 9.0 / 5.0 + 32.0

def band_f(lo_c, hi_c):
    """Celsius band -> Fahrenheit band keeping the 4-interval invariant.
    Snap lo DOWN to a multiple of 5 (a multiple of the step clips Freezer's top),
    then take the smallest step from 5/10/20 whose 4 intervals cover the span."""
    lo, hi = to_f(lo_c), to_f(hi_c)
    lo = math.floor(lo / 5.0) * 5
    for step in (5, 10, 20):
        if lo + 4 * step >= hi:
            return lo, lo + 4 * step, step
    step = int(math.ceil((hi - lo) / 4.0 / 5.0) * 5)
    return lo, lo + 4 * step, step

def parse_thermostat(s):
    """'[digits]C|F' -> (setpoint or None, unit). Bare 'C'/'F' = unit only, no line."""
    m = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)?\s*([CF])\s*", s, re.I)
    if not m:
        sys.exit("gen-chart.py: --thermostat must be digits + C|F (e.g. 3C, 70F, -10C) "
                 "or a bare C|F for the unit with no line — got '%s'" % s)
    return (float(m.group(1)) if m.group(1) is not None else None), m.group(2).upper()

def parse_night(s, default_year):
    """'7/18' | '07/18/2026' | '2026-07-18' -> date."""
    s = s.strip()
    for fmt in ("%m/%d/%Y", "%m/%d", "%Y-%m-%d"):
        try:
            d = datetime.datetime.strptime(s, fmt).date()
            return d.replace(year=default_year) if fmt == "%m/%d" else d
        except ValueError:
            pass
    sys.exit("gen-chart.py: can't read night '%s' — use 7/18, 07/18/2026 or 2026-07-18" % s)

# ---------- config ----------
# scale + dehumidifier are filled from the CLI (see bottom); brand is the title base.
CFG = dict(brand="Cabin climate")

# CSV filename prefix -> scale. Inferred from the name unless --scale is given.
PREFIX_TO_SCALE = {
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

# One colour per overlaid night, in date order, matched by the legend. Deliberately
# avoids the humidity blue and the thermostat green so nothing reads as another element.
NIGHT_COLORS = ["#d62728", "#ff7f0e", "#7b3294", "#8c564b", "#e377c2", "#17becf", "#bcbd22"]

# --measure both keeps red=temperature / blue=humidity (the axis titles are coloured to
# match) and tells the overlaid periods apart by dash pattern instead of by colour.
DASHES = [None, "9 5", "2 4", "12 4 2 4", "6 3 2 3"]

def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def build_svg(lines, cfg, anchor):
    """lines = [{"times": [...], "values": [...], "axis": "L"|"R"}, ...].
    Single mode passes one L + one R; overlay passes N on L."""
    L, R = cfg["left"], cfg.get("right")
    dual = R is not None
    all_t = [t for ln in lines for t in ln["times"]]
    # Axis range: honor an explicit WIN_START/WIN_END exactly; otherwise snap the
    # data range out to the enclosing 12h ticks.
    wmin = (WIN_START - anchor).total_seconds() / 3600 if WIN_START else math.floor(min(all_t) / 12) * 12
    wmax = (WIN_END   - anchor).total_seconds() / 3600 if WIN_END   else math.ceil (max(all_t) / 12) * 12
    span = wmax - wmin
    # tick spacing: explicit --xstep wins, else auto (finer ticks for short windows).
    tstep = cfg["xstep"] if cfg.get("xstep") else (12 if span >= 24 else (2 if span > 8 else 1))
    def X(t): return PL + (t - wmin) / (wmax - wmin) * PW
    def scaleY(ax):
        lo, hi = ax["lo"], ax["hi"]
        return lambda v: PB - (max(lo, min(hi, v)) - lo) / (hi - lo) * PH
    YL = scaleY(L)
    YR = scaleY(R) if dual else None
    cy = (PT + PB) / 2
    nticks = int((L["hi"] - L["lo"]) // L["step"])   # shared interval count (L & R aligned)

    p = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
         'viewBox="0 0 %d %d" font-family="%s">' % (W, H, W, H, FONT)]
    p.append('<rect width="%d" height="%d" fill="#fff"/>' % (W, H))

    # shared horizontal gridlines, with left (and in dual mode right) value labels
    for i in range(nticks + 1):
        vl = L["lo"] + L["step"] * i
        y = YL(vl)
        p.append('<line x1="%.1f" y1="%.2f" x2="%.1f" y2="%.2f" stroke="%s"/>' % (PL, y, PR, y, GRID))
        p.append('<text x="%.1f" y="%.2f" text-anchor="end" dominant-baseline="middle" '
                 'font-size="14" fill="%s">%d%s</text>' % (PL-8, y, INK, vl, L["suffix"]))
        if dual:
            vr = R["lo"] + R["step"] * i
            p.append('<text x="%.1f" y="%.2f" text-anchor="start" dominant-baseline="middle" '
                     'font-size="14" fill="%s">%d%s</text>' % (PR+8, y, INK, vr, R["suffix"]))

    # vertical gridlines; 24h clock time, plus the real weekday at midnight in single mode
    def fmt_clock(h):
        m = int(round(h * 60)) % 1440
        return "%02d:%02d" % (m // 60, m % 60)
    t = wmin
    while t <= wmax + 1e-9:
        x = X(t)
        p.append('<line x1="%.2f" y1="%.1f" x2="%.2f" y2="%.1f" stroke="%s"/>' % (x, PT, x, PB, GRID))
        p.append('<text x="%.2f" y="%.1f" text-anchor="middle" font-size="14" fill="%s">%s</text>' % (x, PB+18, INK, fmt_clock(t)))
        # single mode: the real weekday at each midnight. Overlay: only when every
        # overlaid period starts on the same weekday (weeks do, nights don't), and
        # then on every tick, since the ticks needn't land on midnight.
        show_day = (t % 24 == 0) if not cfg.get("overlay") else cfg.get("weekday_ticks")
        if show_day:
            day = (anchor + datetime.timedelta(hours=t)).strftime("%a")
            p.append('<text x="%.2f" y="%.1f" text-anchor="middle" font-size="14" fill="%s">%s</text>' % (x, PB+35, INK, day))
        t += tstep

    # axis borders: left, right, bottom
    for xb in (PL, PR):
        p.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s"/>' % (xb, PT, xb, PB, INK))
    p.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s"/>' % (PL, PB, PR, PB, INK))

    # data lines (clamped to band via scaleY)
    for ln in lines:
        ax = L if ln["axis"] == "L" else R
        Y = YL if ln["axis"] == "L" else YR
        pts = " ".join("%.2f,%.2f" % (X(t), Y(v)) for t, v in zip(ln["times"], ln["values"]))
        dash = ' stroke-dasharray="%s"' % ln["dash"] if ln.get("dash") else ""
        p.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="3" '
                 'stroke-linejoin="round" stroke-linecap="round"%s/>' % (pts, ln.get("color", ax["color"]), dash))

    # thermostat setpoint — solid bold green reference line on the temperature axis,
    # already expressed in the axis unit.
    ts = cfg.get("thermostat")
    if ts is not None and L["src"] == "temp":
        ty = YL(ts)
        label = cfg["thermostat_label"]
        p.append('<line x1="%d" y1="%.2f" x2="%d" y2="%.2f" stroke="%s" stroke-width="3.5"/>' % (PL, ty, PR, ty, GREEN))
        p.append('<text x="%d" y="%.2f" text-anchor="end" font-size="14" fill="%s">%s</text>' % (PR-6, ty-5, GREEN, label))

    # title + subtitle
    p.append('<text x="%d" y="30" text-anchor="middle" font-size="24" font-weight="bold" fill="%s">%s</text>' % (W//2, INK, esc(cfg["title"])))
    p.append('<text x="%d" y="52" text-anchor="middle" font-size="18" fill="%s">%s</text>' % (W//2, GREY, esc(cfg["subtitle"])))
    # axis titles, 18pt, colored to match their line
    p.append('<text x="18" y="%.1f" transform="rotate(-90 18 %.1f)" text-anchor="middle" font-size="18" fill="%s">%s</text>' % (cy, cy, L["color"], esc(L["title"])))
    if dual:
        rx = W - 18
        p.append('<text x="%d" y="%.1f" transform="rotate(90 %d %.1f)" text-anchor="middle" font-size="18" fill="%s">%s</text>' % (rx, cy, rx, cy, R["color"], esc(R["title"])))

    # legend (top-right, inside the plot's empty upper corner): the two measures in
    # single mode, one entry per night — colour-matched to its line — in overlay.
    if cfg.get("overlay"):
        entries = [(ln["label"], ln.get("color", L["color"]), ln.get("dash")) for ln in lines]
        lx = PR - 185
    else:
        entries = [("Temperature", L["color"], None), ("Humidity", R["color"], None)]
        lx = PR - 150
    ly = PT + 18
    for label, color, dash in entries:
        da = ' stroke-dasharray="%s"' % dash if dash else ""
        p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="3"%s/>' % (lx, ly, lx+22, ly, color, da))
        p.append('<text x="%.1f" y="%.1f" dominant-baseline="middle" font-size="13" fill="%s">%s</text>' % (lx+28, ly, INK, esc(label)))
        ly += 20

    p.append('</svg>')
    return "\n".join(p)

# ---- CLI: see the Usage block in the module docstring ----
ap = argparse.ArgumentParser(
    usage="gen-chart.py --csv FILE [FILE ...] [--scale NAME] [--eva 1|2] "
          "[--thermostat [N]C|F] [--win HH:MM-HH:MM] [--overlay DATES|all] "
          "[--measure temp|hum] [--xstep HOURS] [--title TEXT]")
ap.add_argument("--csv", nargs="+", required=True, metavar="FILE",
                help="logger CSV(s); scale inferred from the filename prefix")
ap.add_argument("--scale", choices=sorted(BANDS), help="axis band to draw against")
ap.add_argument("--eva", choices=["1", "2"], help="Eva-dry count (required for Indoor Storage)")
ap.add_argument("--thermostat", metavar="[N]C|F",
                help="setpoint + axis unit, e.g. 70F, 3C; bare C|F = unit only, no line")
ap.add_argument("--win", metavar="START-END", help="X-axis window, e.g. 22:00-08:00 (end <= start rolls next day)")
ap.add_argument("--overlay", metavar="DATES", help="period start dates (7/18,7/19) or 'all'")
ap.add_argument("--days", type=int, default=1, metavar="N",
                help="days the window spans, for periods longer than one day (default: 1)")
ap.add_argument("--measure", choices=["temp", "hum", "both"], default="temp",
                help="overlay series: temp (default), hum, or both on a dual axis")
ap.add_argument("--xstep", type=float, metavar="HOURS", help="hours between X-axis ticks (default: auto by span)")
ap.add_argument("--title", metavar="TEXT", help="override the chart title, e.g. 'Freezer (Level 3)'")
args = ap.parse_args()
SRCS = args.csv

stem = os.path.splitext(os.path.basename(SRCS[0]))[0]
CFG["scale"] = args.scale or next((sc for pre, sc in PREFIX_TO_SCALE.items() if stem.startswith(pre)), None)
if CFG["scale"] is None:
    sys.exit("gen-chart.py: can't infer the scale from '%s' — pass --scale, or name the file "
             "one of %s + '-<date>.csv'" % (os.path.basename(SRCS[0]), " | ".join(PREFIX_TO_SCALE)))

if CFG["scale"] == "Indoor Storage" and not args.overlay:
    if args.eva is None:
        sys.exit("gen-chart.py: Indoor Storage needs the Eva-dry count — pass --eva 1 or --eva 2")
    CFG["dehumidifier"] = "Single Eva-dry" if args.eva == "1" else "Double Eva-dry"

b = BANDS[CFG["scale"]]

# --thermostat carries both the setpoint and the temperature axis unit. Omitted ->
# the band's own setpoint on a Celsius axis (unchanged from before this flag existed).
if args.thermostat:
    setpoint, CFG["unit"] = parse_thermostat(args.thermostat)
    label = None if setpoint is None else "Thermostat %g °%s" % (setpoint, CFG["unit"])
else:
    CFG["unit"] = "C"
    if b.get("thermostat_f") is not None:                   # °F setpoint on the °C axis, as before
        setpoint = (b["thermostat_f"] - 32) * 5.0 / 9.0
        label = "Thermostat %d °F" % b["thermostat_f"]
    elif b["thermostat"] is not None:
        setpoint = b["thermostat"]
        label = "Thermostat %d °C" % b["thermostat"]
    else:
        setpoint, label = None, None
CFG["thermostat"], CFG["thermostat_label"] = setpoint, label

# temperature band in the chosen unit; humidity is unit-free
if CFG["unit"] == "F":
    t_lo, t_hi, t_step = b.get("temp_f") or band_f(b["temp"][0], b["temp"][1])
    t_title, t_suffix = "Temperature (°F)", "°"
else:
    t_lo, t_hi, t_step = b["temp"]
    t_title, t_suffix = "Temperature (°C)", "°"

# --win overrides the in-source WIN_START/WIN_END, anchored to the data.
if args.win:
    try:
        s_str, e_str = args.win.split("-")
        s_h, s_m = [int(x) for x in s_str.strip().split(":")]
        e_h, e_m = [int(x) for x in e_str.strip().split(":")]
    except ValueError:
        sys.exit("gen-chart.py: --win must look like 22:00-08:00")

if args.overlay and not args.win:
    sys.exit("gen-chart.py: --overlay needs --win to say which window each night covers")

TEMP = dict(title=t_title, lo=t_lo, hi=t_hi, step=t_step, suffix=t_suffix, color="#d62728", src="temp")
HUM  = dict(title="Humidity (%RH)", lo=b["hum"][0], hi=b["hum"][1], step=b["hum"][2],
            suffix="%", color="#2166c4", src="hum")

if args.overlay:
    # ---- overlay: N nights of one measure, re-anchored onto a shared window ----
    CFG["overlay"] = True
    pools = [(src, read_pts(src)) for src in SRCS]
    years = [p[0][0].year for _, p in pools if p]
    win_h = s_h + s_m / 60.0
    span_h = (e_h + e_m / 60.0) - win_h
    if span_h <= 0: span_h += 24
    span_h += (args.days - 1) * 24

    if args.overlay.strip().lower() == "all":
        cand = set()
        for _, pts in pools:
            d = pts[0][0].date()
            while d <= pts[-1][0].date():
                cand.add(d); d += datetime.timedelta(days=1)
        nights = sorted(cand)
    else:
        nights = [parse_night(x, years[0]) for x in args.overlay.split(",")]

    lines, used, skipped = [], [], []
    for n in nights:
        ws = datetime.datetime(n.year, n.month, n.day, s_h, s_m)
        we = ws + datetime.timedelta(hours=span_h)
        best, best_src = [], None
        for src, pts in pools:
            seg = [p for p in pts if ws <= p[0] <= we]
            if len(seg) > len(best): best, best_src = seg, src
        if not best:
            skipped.append((n, "no data")); continue
        cover = (best[-1][0] - best[0][0]).total_seconds() / 3600 / span_h
        if args.overlay.strip().lower() == "all" and cover < 0.95:
            skipped.append((n, "%.0f%% coverage" % (cover * 100))); continue
        # x = decimal hours from the night's own midnight, so every night lands on the
        # same window (e.g. 22.0 -> 32.0) and fmt_clock still prints real clock times.
        base = datetime.datetime.combine(n, datetime.time())
        times = [(p[0] - base).total_seconds() / 3600 for p in best]
        temps = [to_f(p[1]) if CFG["unit"] == "F" else p[1] for p in best]
        hums  = [p[2] for p in best]
        tag = n.strftime("%a %b %-d")
        if args.measure == "both":
            # colour carries the measure (matching the axis titles), dash carries the period
            dash = DASHES[len(used) % len(DASHES)]
            lines.append(dict(times=times, values=temps, axis="L", color=TEMP["color"],
                              dash=dash, label="%s  temp" % tag))
            lines.append(dict(times=times, values=hums, axis="R", color=HUM["color"],
                              dash=dash, label="%s  humidity" % tag))
        else:
            lines.append(dict(times=times, values=temps if args.measure == "temp" else hums,
                              axis="L", color=NIGHT_COLORS[len(used) % len(NIGHT_COLORS)],
                              label=tag))
        used.append((n, os.path.basename(best_src), cover))
    if not lines:
        sys.exit("gen-chart.py: --overlay matched no nights with data")

    CFG["left"] = TEMP if args.measure in ("temp", "both") else HUM
    CFG["right"] = HUM if args.measure == "both" else None
    CFG["weekday_ticks"] = len(set(d.weekday() for d, _, _ in used)) == 1
    anchor = datetime.datetime.combine(used[0][0], datetime.time())
    WIN_START = anchor + datetime.timedelta(hours=win_h)
    WIN_END   = WIN_START + datetime.timedelta(hours=span_h)
    d0, d1 = used[0][0], used[-1][0]
    CFG["subtitle"] = "%d %s, %s" % (len(used), "nights" if args.days == 1 else "weeks",
                                     date_range(d0, d1))                  # the legend names them
else:
    # ---- single: one window, temperature + humidity on a dual axis ----
    if args.win:
        peek = load(SRCS[0])                            # unfiltered peek to place the window
        fd = peek[3]                                    # first data date
        first_dt = peek[5] + datetime.timedelta(hours=peek[0][0])   # first data timestamp
        WIN_START = datetime.datetime(fd.year, fd.month, fd.day, s_h, s_m)
        WIN_END   = datetime.datetime(fd.year, fd.month, fd.day, e_h, e_m)
        if WIN_END <= WIN_START:                        # overnight window rolls to the next day
            WIN_END += datetime.timedelta(days=1)
        WIN_END += datetime.timedelta(days=args.days - 1)
        while WIN_END < first_dt:                       # window sits before the data — roll forward
            WIN_START += datetime.timedelta(days=1)
            WIN_END   += datetime.timedelta(days=1)

    times, temps, hums, d0, d1, anchor = load(SRCS[0], WIN_START, WIN_END)
    if CFG["unit"] == "F":
        temps = [to_f(v) for v in temps]
    CFG["left"], CFG["right"] = TEMP, HUM
    lines = [dict(times=times, values=temps, axis="L"),
             dict(times=times, values=hums,  axis="R")]
    used = None
    if CFG["scale"] == "Indoor Storage":
        CFG["subtitle"] = "%s, %s" % (CFG["dehumidifier"], date_range(d0, d1))
    else:
        CFG["subtitle"] = date_range(d0, d1)

CFG["xstep"] = args.xstep

# title
if CFG["scale"] in ("Fridge", "Freezer"):
    CFG["title"] = CFG["scale"]                          # equipment: the scale name IS the title
else:
    CFG["title"] = "%s (%s)" % (CFG["brand"], CFG["scale"])
if args.title:
    CFG["title"] = args.title                            # per-run override (e.g. thermostat level)

svg = build_svg(lines, CFG, anchor)

# Output: SVG beside the CSV. single -> same base name; overlay -> the scale's slug
# (cabin-outdoors.svg, cabin-indoor-storage.svg, freezer.svg), which is the short
# topical name these charts get published under.
if args.overlay:
    slug = CFG["scale"].lower().replace(" ", "-")
    if CFG["scale"] in ("Indoor Storage", "Outdoors"):
        slug = "cabin-" + slug
    OUT = os.path.join(os.path.dirname(os.path.abspath(SRCS[0])), slug + ".svg")
else:
    OUT = os.path.splitext(SRCS[0])[0] + ".svg"
with open(OUT, "w") as f: f.write(svg)

if used:
    for d, src, cov in used:
        print("  %s  %-28s %3.0f%%" % (d.strftime("%m/%d"), src, cov * 100))
    print("periods:", len(used), "-> wrote", OUT)
else:
    print("points:", len(times), "range:", d0, "->", d1, "-> wrote", OUT)
