# GettingLost — working agreement

## READ THIS AT THE START OF EVERY SESSION

**ALWAYS DO THIS: follow the rules in this file, and in the two files it points to. All of
them, every time.**

They are not preferences to weigh against my own judgment in the moment — they are the
agreement. Every rule exists because breaking it already cost Pierre something. Breaking one
again costs his time, costs limited resources, and irritates him — and it makes writing rules
pointless, which is the worst outcome of the three.

## 1. How to work with Pierre

**`~/Claude/working-with-pierre.md`** — loaded automatically in every project via
`~/.claude/CLAUDE.md`. FIND ≠ FIX, plan before implementing, answer short, opinions vs
verdicts, park small findings, work from fresh data, code conventions. Those rules apply
here in full and are not repeated below.

## 2. Where this project's knowledge lives

- **[docs/README.md](docs/README.md)** — the index of everything documented about this site:
  schemas, conventions, renderer behavior, recipes, external APIs, project records. **Read
  the index at the start of any real work, then the specific doc it points to.** Do not
  reconstruct from memory what is written down there.
- **[.claude/toolchain.md](.claude/toolchain.md)** — Claude's setup for this repo:
  session-start validation, permission tiering, one-command-per-Bash-call, inspecting the
  live site, browser-pane gotchas.
- **[docs/todo.md](docs/todo.md)** — parked work. Side issues found mid-task go here.

## 3. Log entries: phone auto-commits, computer defers to Pierre.

*(scoped exception to FIND ≠ FIX and plan-before-implementing)*

Changes under `logs/` (e.g. `logs/fuel-log.json`) follow a device split:

- **On the phone:** when Pierre adds/updates a log entry, Claude does the whole thing
  automatically — `git add` → commit → `git push` to `main`, no confirmation step. Standing
  authorization so a voice-dictated entry persists to GitHub without extra taps.
- **On the computer:** Claude makes/edits the `logs/` entry and **STOPS**. Pierre pushes.

Applies **only** to changes under `logs/`. Everything outside `logs/` follows the normal
rules — find ≠ fix, plan before acting, confirm before pushing. Detect device from the
runtime environment (computer = local shell + filesystem present).

## 4. Site rules

- **URLs are always `https://`.** When copying a URL from any source into the site data,
  rewrite `http://` → `https://`. Never curl/fetch/test a plain `http://` URL — upgrade the
  scheme first.
- **Render, don't second-guess.** A renderer renders the block's content as-is; content and
  structure are the author's responsibility. See
  [docs/rendering/blocks.md](docs/rendering/blocks.md).
- **Fix the data, not with legacy-tolerant code.** Migrate all the data to the new shape and
  write for that shape only. The site is deliberately small so this stays cheap.
