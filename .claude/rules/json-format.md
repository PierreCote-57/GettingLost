# JSON house format

Applies to every repo-authored JSON file under `media/data/**` and `logs/`.
Established 2026-07-19.

**TAB-indented, pretty-printed, one field per line.** Verified byte-identical to IntelliJ's
reformat, so Claude's scripts and Pierre's editor never fight over a file.

**Write through the shared helper `local/tools/jsonio.py` (`load` / `save`), never a bare
`json.dump`.**

**Route even single-field edits through python.** A load/dump round-trip cannot emit invalid
JSON or a half-applied edit; string-matching with the `Edit` tool can do both.

Why the format: a one-field change becomes a one-line git diff. The old one-line-per-record
format made every edit look like a whole-record rewrite, and IntelliJ can collapse and expand
records in the current shape. Size is irrelevant — gzip eliminates indentation on the wire.

**`local/data/**` is exempt and FROZEN** — historical reference material in whatever format
suited it when captured. Never write there without a specific request from Pierre, and never
reformat it to match the current schema.

Related: [docs/conventions/site.md](../../docs/conventions/site.md).
