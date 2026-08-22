# Charting — CSV logger → SVG → PNG

Turns TempU03 CSV logger data into a chart for the howto-climate gallery.

**Pipeline (as of 2026-07-18):** pure-Python **SVG** generator → Pierre converts
SVG→PNG in IntelliJ (~1 s) → PNG into the gallery. No Chart.js, no CDN, no headless
Chrome, no Pillow. The `.svg` is the source of truth; the `.png` is the gallery
deliverable (the gallery serves raster via Jetpack Photon, which can't resize SVG).

## Files here
- `gen-chart.py` — **the generator.** Every knob is a flag; run `--help` for the full list.
- `<scale-prefix>-<startdate>.csv` — logger data; **the only file that persists.**

## How to draw a chart
1. **Name the CSV** with a scale prefix + start date: `<base>-<YYYY-MM-DD>.csv`,
   base ∈ `cabin-indoor` | `cabin-outdoor` | `fridge` | `freezer`.
2. **Run it** (the path stays in shell history — no `.py` edits):

   ```
   python3 gen-chart.py --csv cabin-indoor-2026-07-13.csv --eva 1
   ```
   - `--csv` takes **one or more** files and is required.
   - **Scale is inferred** from the filename prefix (fails loudly on an unknown name);
     `--scale` overrides it.
   - **Eva-dry count** is `--eva 1|2` (Single|Double) — **required for Indoor Storage,
     ignored otherwise.** Claude asks it once per CSV per session (clickable).
   - Other flags: `--thermostat`, `--win`, `--days`, `--overlay`, `--measure`, `--xstep`,
     `--title`. See [../../docs/recipes/charting.md](../../docs/recipes/charting.md).
   - Writes `<same base>.svg` **beside the CSV**.
3. Tweak; then Pierre makes the PNG in IntelliJ, uploads it to WP, and **deletes the
   svg + png** — only the CSV stays. (Deletions are Pierre's call; no gitignore.)

## The dual-axis cabin-climate format — locked EXCEPT the X axis (2026-07-18)
- **900 × 520**, white bg, black L+R+bottom axis borders, `#e1e0d9` gridlines.
- **Left axis** Temperature °C, red `#d62728`. **Right axis** Humidity %RH, blue
  `#2166c4`. The bands live in `BANDS` in `gen-chart.py`, keyed by scale name — read them
  there. Where a scale has both, each spans **4 intervals** so gridlines coincide (the
  invariant to keep when tuning one); all values **clamp** to their band. A scale with no
  `hum` key draws temperature alone — no right axis, no legend entry — and `--measure hum`
  or `both` exits on it.

- **Thermostat** (Indoor/Outdoors): solid **bold green** `#1a9850` line on the temp
  axis + right-aligned "Thermostat N °C" label.
- Lines width 3, no markers; axis titles 18 pt **colored to match their line**;
  **legend** top-right.
- **X axis is NOT locked** — min, max and step vary per chart and are all flags.
  Real linear time, **24-hour** labels, **real weekday name** under each midnight tick.
  Default range = data range **snapped out to the enclosing 12 h ticks** (start = tick
  at/left of first point, end = tick at/right of last point) — always includes all data,
  with the step auto-picked by span. Narrow a chart with `--win`, set the tick spacing
  with `--xstep`. The in-source `WIN_START`/`WIN_END` are only that default; `--win`
  overrides them.
- **Title** 24 bold, **subtitle** 18 grey. The subtitle's **date range is derived from the
  data**; the only value you supply by hand is the Eva-dry count. `--title` overrides the
  computed title for one run.
- **Title / subtitle rules**, keyed by SCALE:
  - Indoor Storage / Outdoors → title `Cabin climate (<Scale>)`
  - Fridge / Freezer → title is **just** `<Scale>`
  - Indoor Storage subtitle → `<Single|Double> Eva-dry, <date range>`; an overlay →
    `<N> nights, <date range>`; others → `<date range>`
