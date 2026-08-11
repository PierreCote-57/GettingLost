# Charting system

Charting system that turns TempU03 **CSV logger data** (id TZ0325122310 — one point
every 10 min: Date, Time, Temperature(C), Humidity(%RH)) into a chart for the
**howto-climate** blog gallery. Started 2026-07-13; **rebuilt as an SVG pipeline 2026-07-18.**

**Location: `local/charting/`.** Key files:
- `gen-chart.py` — **THE generator.**
  `python3 gen-chart.py <csv> [eva:1|2] [--win HH:MM-HH:MM] [--xstep HOURS] [--title TEXT]`.
- `<location>-<startdate>.csv` — logger data; **the only file that persists.**
- `README.md` — canonical how-to; read first.
- (Legacy Chart.js `cabin-temperature.*` + calibration PDF + old CSVs — deleted 2026-07-18.)

## Pipeline (2026-07-18): Python → SVG → IntelliJ PNG
Pure-Python SVG generation — **no Chart.js, no CDN, no headless Chrome, no Pillow**
(the old raster pipeline is retired). Claude runs `gen-chart.py` → `.svg`; **Pierre
converts SVG→PNG in IntelliJ (~1 s)** and drops the PNG into the gallery. The `.svg`
is source of truth; the gallery needs raster because it serves via Jetpack Photon
(`i0.wp.com …?fit=w,h`), which can't resize SVG (and WP blocks SVG uploads). See
[docs/schema/image.md](../schema/image.md), [docs/rendering/blocks.md](../rendering/blocks.md).

## Run flow (2026-07-18) — CLI, one CSV per session
`python3 gen-chart.py <csv> [eva:1|2] [--win …] [--xstep …] [--title …]`. One CSV at a
time; the full command lives in shell history so the `.py` is never edited between
sessions — **every per-chart knob is a flag.**
- **Location is INFERRED from the CSV filename prefix** (`cabin-indoor`→Indoor Storage,
  `cabin-outdoor`→Outdoors, `fridge`→Fridge, `freezer`→Freezer). Not asked. Unknown
  prefix → fail loudly. CSV must be named `<prefix>-<YYYY-MM-DD>.csv`.
- **Eva-dry** = 2nd arg (`1`=Single, `2`=Double); **required for cabin-indoor**, ignored
  else. Claude asks it via **clickable AskUserQuestion ONCE per CSV per session** (not
  every regen) and reuses it. NOTE: this SUPERSEDES the old "ask every generation" rule —
  now location isn't asked at all and eva-dry is asked once per CSV.
- **Output**: `<same base>.svg` written **beside the CSV**.

Lifecycle: **only the CSV persists.** Generate → tweak → Pierre makes the PNG (IntelliJ),
uploads to WP, then **deletes svg + png**. Deletions are Pierre's call — no `.gitignore`.

Title/subtitle rules (in gen-chart.py):
- cabin-indoor / cabin-outdoor → title `Cabin climate (<Location>)`
- Fridge / Freezer → title is **just** `<Location>`
- Indoor subtitle → `<Single|Double> Eva-dry, <date range>`; others → `<date range>`
- **Subtitle date range is derived from the data** (first→last logged date); never ask it.
- **`--title TEXT` overrides the computed title for one run** (added 2026-07-19). For
  per-run equipment settings that aren't a property of the location — first use was
  `--title "Freezer (Level 3)"` for a freezer thermostat-level run. Do NOT hardcode a
  level into `BANDS`; the level varies run to run, the band doesn't. Omitted → default
  title rules above are unchanged.

## LOCKED dual-axis cabin-climate format (finalized 2026-07-18)
- **900 × 520**, white bg, black left+right+bottom borders, `#e1e0d9` gridlines.
- **Left axis** Temp °C red **`#d62728`**; **right axis** Humidity %RH blue **`#2166c4`**.
  **Per-location bands** (`BANDS` in gen-chart.py) — where a location has both, each is
  **4 intervals** so gridlines coincide; all values **clamp** to band (no interpolation
  at 10-min cadence):

  | Location | Temp | Humidity | Thermostat |
  |---|---|---|---|
  | Indoor Storage | 0–40 by 10 | 20–60 by 10 | 6 °C |
  | Outdoors | 10–30 by 5 | 30–70 by 10 | 20 °C |
  | Fridge | 0–20 by 5 | none | — |
  | Freezer | −20–0 by 5 | none | — |

  **Fridge and Freezer carry no humidity** (decided 2026-08-09): no `hum` key in `BANDS`,
  so the series, the right axis, its title and its legend entry are all absent and the
  chart draws temperature alone. `--measure hum` or `both` exits on those two locations.

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
