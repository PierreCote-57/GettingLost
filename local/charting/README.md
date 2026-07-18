# Charting — CSV logger → SVG → PNG

Turns TempU03 CSV logger data into a chart for the howto-climate gallery.

**Pipeline (as of 2026-07-18):** pure-Python **SVG** generator → Pierre converts
SVG→PNG in IntelliJ (~1 s) → PNG into the gallery. No Chart.js, no CDN, no headless
Chrome, no Pillow. The `.svg` is the source of truth; the `.png` is the gallery
deliverable (the gallery serves raster via Jetpack Photon, which can't resize SVG).

## Files here
- `gen-chart.py` — **the generator.** `python3 gen-chart.py <csv> [eva]`.
- `<location>-<startdate>.csv` — logger data; **the only file that persists.**

## How to draw a chart
1. **Name the CSV** with a location prefix + start date: `<base>-<YYYY-MM-DD>.csv`,
   base ∈ `cabin-indoor` | `cabin-outdoor` | `fridge` | `freezer`.
2. **Run it** (one CSV per session; the path stays in shell history — no `.py` edits):

   ```
   python3 gen-chart.py cabin-indoor-2026-07-13.csv 1
   ```
   - **Location is inferred** from the filename prefix (fails loudly on an unknown name).
   - **Eva-dry count** is the 2nd arg (`1`=Single, `2`=Double) — **required for
     `cabin-indoor`, ignored otherwise.** Claude asks it once per CSV per session (clickable).
   - Writes `<same base>.svg` **beside the CSV**.
3. Tweak; then Pierre makes the PNG in IntelliJ, uploads it to WP, and **deletes the
   svg + png** — only the CSV stays. (Deletions are Pierre's call; no gitignore.)

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
