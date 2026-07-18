# Charting — CSV logger → SVG → PNG

Turns TempU03 CSV logger data into a chart for the howto-climate gallery.

**Pipeline (as of 2026-07-18):** pure-Python **SVG** generator → Pierre converts
SVG→PNG in IntelliJ (~1 s) → PNG into the gallery. No Chart.js, no CDN, no headless
Chrome, no Pillow. The `.svg` is the source of truth; the `.png` is the gallery
deliverable (the gallery serves raster via Jetpack Photon, which can't resize SVG).

## Files here
- `gen-chart.py` — **the generator.** `python3 gen-chart.py` → writes `<base>-<start-date>.svg`.
- `cabin-indoor-*.svg` etc. — current output (dual-axis cabin climate chart).
- `TZ0325122310_*.csv` — source data (TempU03, one point every 10 min).
- `Calibration Certificate_*.pdf` — logger calibration.
- `cabin-temperature.html`, `cabin-temperature.template.html`, `cabin-temperature.png` —
  **legacy Chart.js** temp chart, fully superseded by `gen-chart.py` (thermostat line
  ported; clamp is universal; red-out-of-range was dropped by design). Safe to retire
  once the temp chart is confirmed uploaded to the gallery.

## How to draw a chart
1. **Ask Pierre (clickable), then set `CFG` in `gen-chart.py`:**
   - **Location?** → Indoor Storage | Outdoors | Fridge | Freezer → `CFG["location"]`
   - **How many Eva-dry?** (1/2) → `CFG["dehumidifier"]` — **only for Indoor Storage.**
2. `python3 gen-chart.py` → writes `<base>-<start-date>.svg` (auto-named, below).
3. Pierre: SVG→PNG in IntelliJ (makes `<name>.svg.png`), rename to `<name>.png`, drop
   into the howto-climate gallery.

## Filename (auto-derived — never typed)
Lowercase `<location-base>-<start-date>.svg`, start date ISO `YYYY-MM-DD` (sortable;
the full range lives in the subtitle). One Eva-dry config per start date, so the
count is not in the name.

| Location | Base | Example |
|---|---|---|
| Indoor Storage | `cabin-indoor` | `cabin-indoor-2026-07-13.svg` |
| Outdoors | `cabin-outdoor` | `cabin-outdoor-2026-07-13.svg` |
| Fridge | `fridge` | `fridge-2026-07-13.svg` |
| Freezer | `freezer` | `freezer-2026-07-13.svg` |

## Locked format (cabin climate, dual-axis) — finalized 2026-07-18
- **900 × 520**, white bg, black L+R+bottom axis borders, `#e1e0d9` gridlines.
- **Left axis** Temperature °C, red `#d62728`. **Right axis** Humidity %RH, blue
  `#2166c4`. Per-location bands (`BANDS` in `gen-chart.py`) — both always **4 intervals**
  so gridlines coincide; all values **clamp** to their band (no interpolation needed at
  10-min cadence):

  | Location | Temp | Humidity | Thermostat |
  |---|---|---|---|
  | Indoor Storage | 0–20 by 5 | 20–60 by 10 | 6 °C |
  | Outdoors | 10–30 by 5 | 30–70 by 10 | 20 °C |
  | Fridge | 0–20 by 5 | 30–70 by 10 | — |
  | Freezer | −20–0 by 5 | 30–70 by 10 | — |

- **Thermostat** (Indoor/Outdoors): solid **bold green** `#1a9850` line on the temp
  axis + right-aligned "Thermostat N °C" label.
- **Two lines** width 3, no markers; axis titles 18 pt **colored to match their line**;
  **legend** top-right.
- **X axis** real linear time, gridline every **12 h**, **24-hour** labels
  (`00:00`/`12:00`), **real weekday name** under each midnight tick. Default range =
  data range **snapped out to the enclosing 12 h ticks** (start = tick at/left of first
  point, end = tick at/right of last point) — always includes all data. Narrow one
  chart by setting `WIN_START` / `WIN_END`.
- **Title** 24 bold, **subtitle** 18 grey. Subtitle **date range derived from the
  data**; only manual subtitle input is the Eva-dry count.
- **Title / subtitle rules:**
  - Indoor Storage / Outdoors → title `Cabin climate (<Location>)`
  - Fridge / Freezer → title is **just** `<Location>`
  - Indoor Storage subtitle → `<Single|Double> Eva-dry, <date range>`; others → `<date range>`
