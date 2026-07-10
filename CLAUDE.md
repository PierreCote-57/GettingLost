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

---
See the memory `feedback-working-style` for the fuller collaboration notes
(git workflow, response style, curl format, data-migration preference, etc.).
