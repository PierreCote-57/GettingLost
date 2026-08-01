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
- **[docs/toolchain.md](docs/toolchain.md)** — Claude's setup for this repo:
  session-start validation, permission tiering, one-command-per-Bash-call, inspecting the
  live site, browser-pane gotchas.
- **[docs/todo.md](docs/todo.md)** — parked work. Side issues found mid-task go here.

**`docs/skills/` holds procedures to FOLLOW, not background to read.** Treat a file there
exactly as if it were an installed skill: when Pierre asks for the thing it covers, open it
and follow it step by step. Today that is
[docs/skills/keyword-validation.md](docs/skills/keyword-validation.md) — run it when he asks
for a keyword validation pass, or asks about keyword drift or the vocabulary generally.

**Two conventions govern actions rather than describing the site, so check them before
acting, not after:** [docs/conventions/json-format.md](docs/conventions/json-format.md)
before writing any JSON under `media/data/**` or `logs/`, and
[docs/conventions/keywords.md](docs/conventions/keywords.md) before touching `tags` in one.

Nothing but genuine configuration lives in `.claude/` — content that gets edited belongs in
`docs/`, where editing it doesn't need a permission dialog (2026-08-01).

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

## 4. After a structural session, tell Pierre to run a backup

He runs the **free** UpdraftPlus, which has no scheduling — a backup only happens when he
starts one by hand, and nothing in the pipeline takes one. So end any session that changed
the site structurally with a one-line reminder. Not a question, not an offer to do it.

Structural means a schema migration, a bulk rewrite of data files, a slug or filename change
across many objects, template or theme edits, or anything that moved or deleted pages.
Adding a page, editing content, or fixing one record is not structural.

It lives here, in the always-loaded file, because it is a thing to be *said at the right
moment* — buried in a conventions doc it was missed through both the schema unification and
the slug rebuild.

## 5. Site rules

- **URLs are always `https://`.** When copying a URL from any source into the site data,
  rewrite `http://` → `https://`. Never curl/fetch/test a plain `http://` URL — upgrade the
  scheme first.
- **Render, don't second-guess.** A renderer renders the block's content as-is; content and
  structure are the author's responsibility. See
  [docs/rendering/blocks.md](docs/rendering/blocks.md).
- **Fix the data, not with legacy-tolerant code.** Migrate all the data to the new shape and
  write for that shape only. The site is deliberately small so this stays cheap.
