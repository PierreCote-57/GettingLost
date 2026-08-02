# Claude toolchain notes

How Claude's tooling is set up for this project: permissions, session-start checks,
and the browser gotchas that have caused false diagnoses. Site knowledge is not here —
see [docs/README.md](../docs/README.md).

The rules Claude must follow live in [CLAUDE.md](../CLAUDE.md). This file is the
supporting detail behind a few of them.

## Session-start validation

Validate all three access points at the start of every session, before any work.

**1. Pictures folder** — `~/Pictures/GettingLost`, checked with `ls`. A local folder, not
Google Drive. Granted via `additionalDirectories` with explicit `Bash(...)` allow rules,
so it should not prompt. If it does, the settings are wrong.

**2. WordPress MCP** — site `255518505` (gettinglostonvi.wpcomstaging.com). Load
`wpcom-user-sites` via ToolSearch and call it to confirm the connection.

**3. FileBird REST API** — endpoint, curl format and param quirks are in
[docs/reference/filebird-api.md](../docs/reference/filebird-api.md). **The bearer token is
deliberately not in this repo** — it is in Claude's `feedback-session-start` memory. A
healthy response is `{"success":true,"data":{"folders":[…]}}` with the Images (id 52) and
Data (id 56) roots.

**Why:** Claude repeatedly forgot how to reach FileBird — tried the WP MCP tools, searched
transcripts, guessed endpoints. Use the documented commands; don't rediscover them.

## Bash calls

**One command per Bash call.** Chaining with `&&`, `;`, pipes or newlines trips a
permission gate on Pierre's machine and adds friction to every step.

**curl is URL-first** — `curl "<url>" -s -H "…"`. A flag before the URL breaks the
allow-rule glob. Piping to anything is a different command string and needs its own rule.

Chaining is worse than it looks: a compound line has to match the allow rule *as a whole*,
and a changing commit message defeats the match every time. So the `logs/` auto-commit is
three separate calls — `git add …`, then `git commit …`, then `git push` — never one line.
Individual commands hit stable prefix rules (`git add:*`, `git commit:*`, `git push:*`), so
"always allow" actually sticks.

When several shell steps are needed, **write a script into the scratchpad and run it by
path**. Do not reach for a long inline `python3 -c` or a heredoc: multi-line commands don't
match the `Bash(python3:*)` rule, so they prompt every time, and each approval appends a
dead exact-command entry to `settings.local.json`.

## Settings tiering

Consolidated 2026-07-19 into a deliberate tiering. Keep it this way; don't let
`settings.local.json` re-bloat with session one-offs.

| File | Holds |
| --- | --- |
| `~/.claude/settings.json` (global) | project-agnostic only: theme + general-tool Bash allows (`cd`, `curl`, `env`, `find`, `git`, `grep`, `ls`, `mkdir`, `python3`, `touch`), all `:*` except `env` |
| `.claude/settings.json` (project, committed) | GettingLost-specific: `Read`/`Edit`/`Write`, the `~/Pictures/GettingLost` `additionalDirectories` grant, and destructive verbs (`cp`/`mv`/`rm`) **path-scoped** to that folder |
| `.claude/settings.local.json` (project, private) | MCP servers + `WebFetch(domain:*)`/`WebSearch` + a few Bash extras. Sorted, grouped (MCP / Web / Bash), blank-line separated |

Placement rules:

- **Two gates.** `additionalDirectories` is the path boundary — it governs Read/Edit/Write
  and keeps Bash from refusing out-of-workspace. The `allow` list is per-command
  prompt-suppression. Bash is gated by pattern-match, *not* by the path boundary, so
  destructive verbs are path-scoped in the pattern itself.
- **Use the `:*` idiom** (`Bash(ls:*)`) — the structured "command + any args" matcher. The
  naive space-glob `Bash(ls *)` misses bare `ls` and over-matches compound strings.
- Read-only verbs generalize to `:*` in global. Destructive verbs (`rm`/`mv`/`cp`) stay
  path-scoped.
- **MCP whole-server grants use the bare server id** (`mcp__<server>`), no wildcard — MCP
  rules don't support `*`.
- **Connector MCP servers carry opaque GUIDs** (wpcom `7d14df43…`, github `820e7577…`,
  dropbox `4474e9cc…`) that change if a connector is removed and re-added, silently
  breaking the rule. Named servers (`claude-in-chrome`, `visualize`) are stable.
- `awk`/`sed`/`date` are deliberately excluded from the allow-list — use `python3`, the
  `Edit` tool, and the session-provided date instead.

Findings from a long "why does it keep asking?" session (2026-07-10):

- The Bash allow wildcard is **colon-form** — `Bash(git commit:*)`. The space form
  `Bash(git commit *)` does not match and keeps prompting.
- A **trailing comma anywhere in `settings.local.json` makes it invalid JSON**, so the
  harness can't persist new "Always allow" rules — approvals silently fall back to session
  memory and vanish on restart. Keep the file valid.
- The permission prompt's **default button is "Allow once" (⌘↵)**, not Always allow.
  Pressing Enter never persists a rule.
- `Edit` and `Write` in the allow list cover files **anywhere on the filesystem**, not just
  the project directory — no per-path Bash wildcards needed to edit outside the repo.
- `Bash(* ~/path/*)` with a **leading** wildcard does not work. The matcher needs a concrete
  command prefix, e.g. `Bash(ls ~/path/*)`.
- **Writing into `.claude/` prompts anyway** (2026-07-31) — bare `Write` in the allow list
  does not cover it, since a rule letting Claude write its own config and rules would be
  self-granting. This file moved to `docs/` for that reason. Never put a new doc under
  `.claude/` because it wants to be always-loaded: **durable knowledge goes in `docs/`, and
  anything that must load every session goes in `CLAUDE.md`** — an ordinary repo file that
  writes without a prompt. Touch `.claude/` only when Pierre asked for that file by name,
  where the prompt is expected rather than an interruption.
- **`.claude/` now holds nothing but `settings.json` and `settings.local.json`**
  (2026-08-01). The rules and the skill moved to `docs/conventions/` and `docs/skills/`,
  pointed at from `CLAUDE.md`. What was lost is only the `/keyword-validation` slash command
  and its description-based auto-trigger — Pierre has never used a slash command, and the
  keyword rule forbids running that pass unprompted anyway. What was gained is that the
  content edits without a permission dialog, which is where all the churn actually is.

## Image work

Pillow is installed (`from PIL import Image, ImageDraw`) — resize, rotate and straighten,
crop, highlight and annotate. Do image work with Python scripts run via Bash.

## Inspecting the live site

**Claude can ask for a Chrome window at any time — Pierre encourages it.** Measure the
running site instead of reasoning blind about CSS/DOM.

**Why:** during the mini-gallery lightbox work, two rounds of speculative CSS tweaks
changed nothing. Loading the live page and reading computed styles, `getBoundingClientRect`
and `elementFromPoint` found both real bugs in one shot each — flexbox `min-height:auto`
letting the image ignore `max-height:75vh`, and the WP admin bar (z-index 99999) covering
the overlay. Measurement beat theorizing.

- The site is remote (wpcomstaging), so use the **claude-in-chrome MCP**, not a local
  preview. Load tools via ToolSearch; `tabs_context_mcp{createIfEmpty:true}` binds the tab
  group.
- `javascript_tool` is the workhorse. Return `JSON.stringify(...)` — a bare async IIFE
  serializes as `{}`.
- **Don't load many full-res images in a loop.** Sweeping all 21 `listing-pictures` photos
  through the lightbox froze the renderer (CDP timeout). Use a synthetic tall SVG data-URL
  (800×3000) to test worst-case portrait sizing.
- Add `?nocache=1` when re-checking after a push; the deployed `gettinglost.jst` can be
  browser-cached. Confirm deploys with a fresh `curl` of the live `.jst` too.
- Verify a candidate fix live — inject the CSS, re-measure — *before* editing the source.

**Don't call something broken from a screenshot alone.** 2026-07-04: two how-to cards were
read as "missing images / broken links" from a screenshot when a `curl` already run showed
all three images HTTP 200 (raw + Photon). The cards were fine. Recall existing model facts
before diagnosing, too — `featuredImage` is intentionally grid/list-only and never shown
atop a page ([docs/schema/image.md](../docs/schema/image.md)), so a bare page hero is
by design, not a bug.

## Browser pane gotchas

These apply to the **in-app Claude Browser pane** (`mcp__Claude_Browser__*`), which is a
different surface from the real logged-in Chrome above.

**Collapsed viewport.** The pane can render at ~0–60px — seen 2026-07-21 with
`document.body`/`html` at `offsetWidth: 0` and `<main>` at 60px. Every
`getBoundingClientRect().width` then reads ~0, which looks exactly like a real
width-collapse bug but is a tooling artifact. **Before trusting any width measurement, call
`resize_window` with `preset:"desktop"` (1280×800) and re-navigate.** This nearly caused a
misdiagnosis of the map-caption "not updating on pan" as a layout break.

**Stale asset cache (2026-07-26).** The pane caches `gettinglost.cst` and other uploads
assets aggressively. After a `.cst`/`.jst` edit is synced live, `getComputedStyle` can
report the *old* rule — seen reporting weight 400 / 17.84px when the live file already had
600 / 1.15rem — which nearly led to "fixing" a non-bug. **To confirm what is actually
served, `curl` the file with a cache-buster (`?cb=…`)** and read the rule from that.
Theme-level `:root` tokens (`--wp--preset--*`) and unedited files are safe to read from the
pane; it's the just-changed uploads asset that goes stale.

The map-in-`<details>` zero-size quirk is a different, genuine thing — see
[docs/rendering/blocks.md](../docs/rendering/blocks.md). Theme tokens:
[docs/conventions/theme-tokens.md](../docs/conventions/theme-tokens.md).
