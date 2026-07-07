# GettingLost — working agreement

## 1. FIND ≠ FIX. Never change anything I didn't ask you to change. (CARDINAL RULE)

When Pierre asks me to **find, look at, investigate, review, describe, or explain**
something, that is **NOT** permission to edit files, run migrations, or change WP.
Report what I found and **STOP**.

- "Look for pending issues" → list them. Do not start fixing one.
- "There was an issue with X" → investigate and explain the issue. Do not patch it.
- Finding a bug is not a request to fix the bug.
- No `Edit` / `Write` / WP change until Pierre explicitly says **go / yes / do it**.

## 2. Plan before implementing.

Pierre works in explicit planning mode. Discuss and propose first; he sees AND
discusses the plan, and usually tunes it, before any code changes. **"What do you
think?" is discuss-only** — evaluate the plan, don't start building. Default to
showing the plan and waiting.

If in doubt about whether I'm authorized to change something: **ask, don't act.**

## 3. Log entries auto-commit. (scoped exception to rules 1 & 2)

When Pierre adds or updates a **log entry under `logs/`** (e.g. `logs/fuel-log.json`),
commit it and push to the working branch **automatically — no confirmation step**.
This is standing authorization for that one case: log change → `git add` → commit →
`git push`, done.

- Applies **only** to changes under `logs/`. Everything outside `logs/` still follows
  rules 1 and 2 (find ≠ fix, plan before acting, confirm before pushing).
- This is intentional so a quick voice-dictated log entry on the phone persists to
  GitHub without extra taps.

## 4. Verify the effect, don't echo the intent.

After any **mutating call to an external system** (WordPress, git, DNS, file moves),
the call returning success is **NOT** proof it did what I asked. I must read the
**actual resulting state** back and compare it to my intent — then report the real
value, flagging any discrepancy, **before** moving on.

- **Never report back the value I requested as if it were the result.** Report the
  value the system actually used, read from its response or a follow-up fetch.
- WP slug example: I asked for `my-post`; WP may return `my-post-2` (collision),
  `chateau` (sanitized `Château`), or silently ignore the field. Validate the slug
  **WP actually assigned**, not the one I typed.
- If the response doesn't reveal the resulting state, do a follow-up read to confirm it.
- Gap between intended and actual → tell Pierre immediately, don't bury it.

---
See the memory `feedback-working-style` for the fuller collaboration notes
(git workflow, response style, curl format, data-migration preference, etc.).
