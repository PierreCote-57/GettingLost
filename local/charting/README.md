# Charting — how to draw a chart (CSV logger → PNG)

Turns TempU03 CSV logger data into a PNG for the blog galleries.
No local node and no numpy on this machine — the pipeline is headless Chrome + Pillow.

## Files here
- `cabin-temperature.template.html` — LOCKED cabin-temp template (edit this for new cabin charts)
- `cabin-temperature.html` — interactive Chart.js version
- `cabin-temperature.png` — sample output (780×520)
- `TZ0325122310_*.csv`, `Calibration Certificate_*.pdf` — source data

## Steps

### 1. Get the data into `TIMES` / `VALS`
The CSV has a metadata block, then a table:
```
Date,Time,Temperature(C),Humidity(%RH)
07/12/2026, 22:28:17, 22.2,53.9
...
```
Skip everything above that header and the `***` separator row. For each data row:
- `TIMES`  = time as **decimal hours** (`HH + MM/60`, e.g. `08:25` → `8 + 25/60`)
- `VALS`   = the `Temperature(C)` value (trim leading spaces)

One point every 10 min is expected — that's why the format is line-only (no markers).

### 2. Copy the template and edit the two blocks at the top
Copy `cabin-temperature.template.html` → a working `*-export.html` (scratchpad is fine).
Edit only:
- `CFG.title`, `CFG.subtitle`
- `CFG.band` — fixed y-axis (cabin = `{lo:15, hi:25}`). Readings outside clamp to the nearest edge.
- `CFG.thermostat` — °C setpoint line (cabin only; from the post's "Furnace set to" caption). `null` = omit.
- `TIMES`, `VALS`

Aspect is 1.5:1 at 780×520 (the `<canvas width height>`). Keep the render `--window-size` width = canvas width.

### 3. Render to PNG at 2× (headless Chrome)
```sh
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --hide-scrollbars \
  --force-device-scale-factor=2 --window-size=780,540 --virtual-time-budget=4000 \
  --screenshot=/abs/scratch/out-2x.png \
  file:///abs/path/to/your-export.html
```
Gives a 1560×1080 PNG (canvas 1560×1040 + a white bottom margin).

### 4. Crop the white margin and halve (Pillow, supersampled = crisp)
```python
from PIL import Image
im = Image.open('/abs/scratch/out-2x.png').convert('RGB')
assert im.crop((0,1040,im.size[0],im.size[1])).getextrema()==((255,255),(255,255),(255,255))  # bottom is white
im.crop((0,0,1560,1040)).resize((780,520), Image.LANCZOS).save('local/charting/<name>.png')
```

### 5. Verify, then that's the deliverable
Open (or read) the PNG to confirm it looks right. The PNG in `local/charting/` is how Pierre
reviews it. On the computer I stop after writing the file — Pierre pushes.

## Locked cabin-temp format (baked into the template)
Fixed 15–25 °C band, clamp-to-nearest-extreme on the **interpolated line** (red flat segments
at an edge = out of range), real linear hourly x-axis with adaptive AM/PM labels
(`niceStep` ≤12 labels; day name on midnight ticks for multi-day), black thermostat setpoint
line + label, line only, white bg, black axes, axis font 14 / title 17 / subtitle 12, 1.5:1.

## To adapt for other chart families (planned)
- **Temp + Humidity, several days (indoor storage):** long window (niceStep widens the axis
  automatically), second series for humidity, no thermostat line.
- **Temp only, a few hours (heating / fridge / freezer):** change `CFG.band` per equipment
  (fridge ~0–10, freezer sub-zero, heating warm), no thermostat line.
