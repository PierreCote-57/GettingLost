# GettingLost — working agreement

## 1. FIND ≠ FIX. Never change anything I didn't ask you to change. (CARDINAL RULE)

**The default is STOP.** Acting requires an explicit instruction to act. A question,
a plan discussion, or my own sense that the next step is "obvious" is **never**
authorization. When in the slightest doubt: answer/propose, then wait.

When Pierre asks me to **find, look at, investigate, review, describe, or explain**
something, that is **NOT** permission to edit files, run migrations, or change WP.
Report what I found and **STOP**.

- "Look for pending issues" → list them. Do not start fixing one.
- "There was an issue with X" → investigate and explain the issue. Do not patch it.
- Finding a bug is not a request to fix the bug.
- **A question is never a go.** "Are you ready?", "Ready to X?", "Can you…?",
  "Could you…?", "Do you know how to…?" are readiness/scoping checks. Answer them,
  propose the approach, and **wait** — do not start the work or write the output.
- Only an explicit imperative authorizes action: **go / yes / do it / make the
  change / parse it now**. Absent one of those, I have not been told to act.
- **Do exactly what's asked — no more.** An instruction that names a limit
  ("the -1 **only**", "**just** page 1", "**one** file", "one at a time") is a
  boundary, not a launch point. Do precisely that scope and **STOP**. Finishing
  the requested step is **not** license to roll forward into the rest (2–9) on my
  own — report and wait for the next go.
- No `Edit` / `Write` / WP change until Pierre explicitly says **go / yes / do it**.

## 2. Plan before implementing.

Pierre works in explicit planning mode. Discuss and propose first; he sees AND
discusses the plan, and usually tunes it, before any code changes. **"What do you
think?" is discuss-only** — evaluate the plan, don't start building. Default to
showing the plan and waiting.

If in doubt about whether I'm authorized to change something: **ask, don't act.**

## 3. Log entries: phone auto-commits, computer defers to Pierre. (scoped exception to rules 1 & 2)

Changes under `logs/` (e.g. `logs/fuel-log.json`) follow a device split:

- **On the phone:** when Pierre adds/updates a log entry, Claude does the whole thing
  automatically — `git add` → commit → `git push` to `main`, no confirmation step. Standing
  authorization so a voice-dictated entry persists to GitHub without extra taps.
- **On the computer:** Claude makes/edits the `logs/` entry and **STOPS**. Pierre pushes.

Applies **only** to changes under `logs/`. Everything outside `logs/` still follows rules 1
and 2 (find ≠ fix, plan before acting, confirm before pushing). Detect device from the
runtime environment (computer = local shell + filesystem present).

## 4. How to work with Pierre — these are HARD RULES, not preferences.

Every rule about how to work with Pierre lives **here**, as a hard rule — not in
memory. Memory loads as background context and does not reliably govern behavior
(proven: the git-state rule below sat in memory, was loaded, and got broken anyway).
So: **when Pierre corrects how I work with him, the fix goes into this file as a hard
rule** — not a new memory note. Memory keeps only the *why*/history.

- **Git state — never assert it without checking, that same turn.** Do not say a
  change is "pushed" / "still needs pushing" / "committed" / "uncommitted" without
  running `git status` / `git log` in the same turn. The session-start git snapshot
  is stale the moment Pierre commits from IntelliJ — treat it as expired. Default to
  **not mentioning push/commit state at all**; don't sign off with "your push."
- **Work from fresh data — never trust cached or snapshot state.** Pierre edits files
  in IntelliJ, moves things in WP/FileBird, and syncs between prompts. Re-fetch
  (`Read`, `git`, `curl`, MCP) before acting on or asserting any state.
- **Park small findings; don't interrupt the big issue with them.** Pierre's method:
  solve the big thing; the little things it turns up get **noted and deferred**, not
  resolved inline. Raising each one as a question is not thoroughness — it derails
  him, costs continuity, and forces him to re-enter the main problem every time.
  So: when a side issue surfaces mid-task, **write it to `docs/todo.md` and keep
  going**. Hand him the list when the current thing is done, or when he asks. Only
  stop for something that actually blocks the current step or would corrupt data.
- **Never down-talk or condescend.** Pierre is a senior engineer who designed this
  system. Don't re-explain his own architecture or already-established context —
  give the one-line answer and stop. No "as you know" filler, no re-teaching basics.
- **No redundant sign-off / manufactured approval.** Once something is decided, don't
  re-wrap it as "are you good with X?" Don't offer to do trivial one-liners he can do
  faster in IntelliJ. Reserve offering for real leverage (bulk/multi-file/lookups).
- **Never offer a local preview.** Pierre checks rendering himself (IntelliJ / the live
  site). Don't spin one up, and don't offer to.
- **Response style:** numbered lists (`1. 2. 3.`), not bullets, so he can reply
  item-by-item. Direct answer first.
- **One command per Bash call** — no `&&`/`;`/pipes/loops/inline scripts (they defeat
  the permission allow-match). **curl is URL-first:** `curl "<url>" <flags>`.
- **Don't shell out to `awk` / `sed` / `date`** — use the alternatives: `python3` for
  CSV/text parsing and date math, the `Edit` tool for in-file changes, and the
  session-provided date for "now." These are deliberately kept out of the permission
  allow-list; reaching for them means an avoidable prompt.
- **Mark unvalidated numbers "to be validated"; never fabricate specs or URLs.**
- **Render, don't second-guess; fix the data, not with legacy-tolerant code.**
- **URLs are always `https://`.** When copying a URL from any source into the
  site data, rewrite `http://` → `https://`. Never curl/fetch/test a plain
  `http://` URL — upgrade the scheme first.

---
See the memory `feedback-working-style` for the *why*/history behind these rules
(and `feedback-*` memories generally). The rules themselves are the ones above —
memory is context, not the source of truth for behavior.
