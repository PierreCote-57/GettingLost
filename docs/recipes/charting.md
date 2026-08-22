# Charting system

Charting system that turns TempU03 **CSV logger data** (id TZ0325122310 — one point
every 10 min: Date, Time, Temperature(C), Humidity(%RH)) into a chart for the
**howto-climate** blog gallery. Started 2026-07-13; **rebuilt as an SVG pipeline 2026-07-18.**

**Location: `local/charting/`.** Key files:
- `gen-chart.py` — **THE generator.** Every knob is a flag; `--help` is the full list:
  `--csv FILE...` (required) `[--scale S] [--eva 1|2] [--thermostat [N]C|F]`
  `[--win HH:MM-HH:MM] [--days N] [--overlay DATES] [--measure temp|hum|both]`
  `[--xstep HOURS] [--title TEXT]`.
- `<scale-prefix>-<startdate>.csv` — logger data; **the only file that persists.**
- `README.md` — the short how-to beside the script; this file is the fuller record.
- `Calibration Certificate_TZ0325122310.pdf` — the logger's calibration certificate.
- (Legacy Chart.js `cabin-temperature.*` and the pre-SVG CSVs — deleted 2026-07-18.)

## Pipeline (2026-07-18): Python → SVG → IntelliJ PNG
Pure-Python SVG generation — **no Chart.js, no CDN, no headless Chrome, no Pillow**
(the old raster pipeline is retired). Claude runs `gen-chart.py` → `.svg`; **Pierre
converts SVG→PNG in IntelliJ (~1 s)** and drops the PNG into the gallery. The `.svg`
is source of truth; the gallery needs raster because it serves via Jetpack Photon
(`i0.wp.com …?fit=w,h`), which can't resize SVG (and WP blocks SVG uploads). See
[docs/schema/image.md](../schema/image.md), [docs/rendering/blocks.md](../rendering/blocks.md).

## Run flow — CLI, every knob a flag
`python3 gen-chart.py --csv <file> [flags]`. The full command lives in shell history so the
`.py` is never edited between sessions — **every per-chart knob is a flag.**
- **`--csv` takes one or more files and is required.** It is not positional.
- **Scale is INFERRED from the CSV filename prefix** (`cabin-indoor`→Indoor Storage,
  `cabin-outdoor`→Outdoors, `fridge`→Fridge, `freezer`→Freezer). Not asked. Unknown
  prefix → fail loudly. CSV should be named `<prefix>-<YYYY-MM-DD>.csv`. **`--scale`
  overrides the inference**, which is what makes an oddly-named CSV usable.
- **Eva-dry** = `--eva 1|2` (Single|Double); **required for Indoor Storage**, ignored
  else. Claude asks it via **clickable AskUserQuestion ONCE per CSV per session** (not
  every regen) and reuses it. NOTE: this SUPERSEDES the old "ask every generation" rule —
  now scale isn't asked at all and eva-dry is asked once per CSV.
- **`--thermostat [N]C|F`** — setpoint as digits + unit (`3C`, `70F`, `-10C`). The unit
  also picks the temperature axis unit, so `70F` draws a Fahrenheit scale; a bare unit
  (`C`/`F`) picks the scale and draws no setpoint line. Omitted → the band's own setpoint
  on a Celsius scale.
- **`--overlay DATES` + `--days N`** — superimpose several periods, each re-anchored to
  the window start; `--win` is required with it. `--measure temp|hum|both` picks the
  series an overlay draws.
- **Output**: `<same base>.svg` written **beside the CSV**.

Lifecycle: **only the CSV persists.** Generate → tweak → Pierre makes the PNG (IntelliJ),
uploads to WP, then **deletes svg + png**. Deletions are Pierre's call — no `.gitignore`.

Title/subtitle rules (in gen-chart.py), keyed by SCALE not by filename:
- Indoor Storage / Outdoors → title `Cabin climate (<Scale>)`
- Fridge / Freezer → title is **just** `<Scale>`
- Indoor Storage subtitle → `<Single|Double> Eva-dry, <date range>`; an overlay →
  `<N> nights, <date range>` with the legend naming each; others → `<date range>`
- **Subtitle date range is derived from the data** (first→last logged date); never ask it.
- **`--title TEXT` overrides the computed title for one run** (added 2026-07-19). For
  per-run equipment settings that aren't a property of the location — first use was
  `--title "Freezer (Level 3)"` for a freezer thermostat-level run. Do NOT hardcode a
  level into `BANDS`; the level varies run to run, the band doesn't. Omitted → default
  title rules above are unchanged.

## The dual-axis cabin-climate format — locked EXCEPT the X axis (2026-07-18)
- **900 × 520**, white bg, black left+right+bottom borders, `#e1e0d9` gridlines.
- **Left axis** Temp °C red **`#d62728`**; **right axis** Humidity %RH blue **`#2166c4`**.
  **The bands themselves are `BANDS` in `gen-chart.py`** — keyed by scale name, in Celsius,
  and not copied here. What governs them:

  - Where a scale has **both** temp and humidity, each spans **4 intervals** so their
    gridlines coincide. This is the invariant to preserve when tuning a band.
  - All values **clamp** to their band — no interpolation, the 10-min cadence is dense enough.
  - **The Fahrenheit band is DERIVED**, to keep that same invariant: convert, snap lo down to
    a multiple of 5, then take the smallest step from 5/10/20 whose 4 intervals cover the span.
  - **A scale may legitimately have no humidity band** — no `hum` key, so the series, the
    right axis, its title and its legend entry are all absent and the chart draws temperature
    alone. `--measure hum` or `both` exits on such a scale. Fridge and Freezer were set that
    way 2026-08-09.

- **Thermostat** (Indoor/Outdoors): solid **bold green** `#1a9850` line on temp axis +
  right-aligned "Thermostat N °C" label.
- Lines width 3, no markers; **axis titles 18 pt, colored to match their line**;
  **legend** top-right. Title 24 bold, subtitle 18 grey (`#6b6b6b`), tick labels 14.
- **X axis — NOT locked; min/max/step vary per chart** (clarified 2026-07-19). It has
  all three knobs and they're plain CLI flags, no `.py` edit:
  - **min + max** = `--win HH:MM-HH:MM` (end ≤ start rolls to the next day; the window
    is anchored to the data's first date and rolls forward if it lands before the data).
  - **step** = `--xstep HOURS`, a float — `0.25` = a tick every 15 min, `12` = every 12 h.
  - In-source `WIN_START`/`WIN_END` still exist but are only a hard-coded default;
    **`--win` overrides them.** Prefer the flag.
  - **Defaults when both are omitted**: range = data range snapped out to the enclosing
    12 h ticks (always includes all data); step auto by span. The old "gridline every
    12 h" line described only this default, not a locked constraint.
  - Labels are **24-hour**, **real weekday** under each midnight tick. `fmt_clock` used
    to hardcode `:00` minutes, so sub-hour ticks all collapsed to a repeated hour
    (`11:00 11:00 11:00`) — **fixed 2026-07-19** to render real minutes; whole-hour
    ticks are byte-identical, so existing cabin charts are unaffected.

## Showing a chart to Pierre

The folder he opens for charting work is **`local/charting/`** (it was `logs/` very early on
2026-07-13; he moved it). Write or overwrite the file there and say it's there — that is the
delivery. Then stop; Pierre pushes.

The general rule, which applies to any rendered output in any project, is in
`~/Claude/working-with-pierre.md` §9.

See [docs/recipes/image-editing.md](image-editing.md) and
[docs/conventions/github-workflow.md](../conventions/github-workflow.md).
