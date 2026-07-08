# BC Rest Areas — parsing plan (handoff note)

**Status:** not started. This note exists so a future session knows what Pierre means
when he says "parse the rest-areas PDF."

## What Pierre wants

Turn the official BC provincial rest-area list (a PDF) into a **structured data file**
so Claude can answer questions like *"I'm at location X heading south on Highway 19A —
what's the next rest stop ahead?"* reliably, without web searches or PDF-parsing each time.

## Source file

- `local/data/bc-rest-areas-list.pdf` — the official BC government rest-area list,
  downloaded by Pierre from:
  https://www2.gov.bc.ca/assets/gov/driving-and-transportation/driving/rest-areas/bc-rest-areas-list.pdf
- The gov site returns **403** to automated fetches, which is why we keep a local copy.

## Deliverable

Write `local/data/bc-rest-areas.json` (structured, one record per rest area) with fields:

```
name            # rest area name
route           # highway, e.g. "19A", "19"
direction       # travel direction / side, if the list specifies it
distance_from   # the "distance from <reference>" text in the list
latitude        # decimal degrees
longitude       # decimal degrees
amenities       # facilities listed (toilets, etc.), if present
```

Also add a top-level `source` / `downloaded` note in the file (or a sibling field)
recording the download date, so we know how fresh the data is.

## How to parse

- No PDF library is installed in the web environment. `pip install pdfplumber`
  (or pymupdf) via the proxy, then extract the table.
- The PDF is a multi-column table; expect messy column splits and coordinates that
  come apart — verify a few known rows after parsing.
- **Sanity-check rows** we already confirmed by web search:
  - *Oyster Bay* — Hwy 19A, ~8 km south of Campbell River, ~49.94 N, -125.15 W.
  - *Roberts Lake* — Hwy 19, ~32 km north of Campbell River, ~50.2238 N, -125.5509 W.
  - *Eve River* — Hwy 19, further north of Roberts Lake.

## Caveats (keep in mind when answering with this data)

- Covers **official provincial rest areas only** — not gas stations, casual pullouts,
  or municipal parks.
- A committed copy freezes at its download date; the gov list updates occasionally.
- "North/south" is a *filter for what's ahead*, anchored to the actual highway the
  person is on — not straight-line nearest, and not pure latitude (roads curve).

## Branch

Work on `claude/rest-stop-location-id-1jxaej` (this branch already contains the PDF).
