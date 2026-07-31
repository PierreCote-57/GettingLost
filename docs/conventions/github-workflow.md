## Repo
- `PierreCote-57/GettingLost` (public, branch `main`)
- GitHub is master for all Pages and Posts

## Claude's Role
- Claude may commit and push when Pierre asks; otherwise Pierre does it from IntelliJ
- Always re-read files before editing — Pierre edits in IntelliJ between prompts without announcing it
- **Pierre makes the push; Claude makes the files.** Nothing reaches GitHub or syncs to WP
  without his explicit push. Agreed 2026-06-30; may evolve as trust builds
- IntelliJ stages deletions automatically on commit — no need to `git rm`

## Sync Timing
- **A push triggers the sync Action** — expected and fine, even for reorganization-only changes
- **WP changes can proceed in parallel with a push.** When Pierre says "pushed, action is
  starting", go ahead with WP nav or other MCP work without waiting for the sync; they are
  independent

## Remote vs Local Sessions
Claude Code **on the web** runs on an ephemeral cloud VM with its own clone, pinned to a
feature branch — the only route to Pierre is push→pull, and nothing else should be pushed
without explicit permission. His preferred flow is the opposite: local CLI, edits landing on
the local drive on `main`, Pierre pushing himself. So in a web session "make the changes on
my local drive, I'll push" is impossible. **Call the mismatch out immediately** rather than
silently following the web config; the right move is to run that work in the local CLI.

## GitHub Token Policy
- No standing token ever
- Pierre supplies a scoped token only for that session when Claude needs to push/touch workflows/trigger Actions, then revokes it
- Workflow-file pushes need "Workflows: read and write" specifically, not just Contents

## Sync Workflows
- `sync.yml` — manual, full overwrite, no diffing
- `sync-on-push.yml` — automatic incremental on push to main; falls back to full sync when push includes file deletions or when `local/` changes (sync.js doesn't trust its own incremental logic after a self-edit); triggers on `pages/**`, `posts/**`, `media/**`, `local/config/**`, `local/sync/**`
- `pull-posts.yml` — manual trigger, runs pull-posts.js to fetch new WP posts into repo, auto-commits and pushes (has `permissions: contents: write`)

## Running the JS Locally
- Node is installed locally (v26.5.0, npm 11.17.0, on PATH since 2026-07-20) — `node --check`,
  `node -e` and dry runs are all fair game
- But `sync.js` and `pull-posts.js` only run **for real** in GitHub Actions, with credentials
  from Secrets (`WP_SITE_URL`, `WP_USER`, `WP_APP_PASSWORD`, `FILEBIRD_TOKEN`) — the secrets
  are not local by design, and GitHub Secrets are write-only so they can't be read back
- **Never design a script to run locally with manual credential entry.** Any new script that
  talks to WP is paired with a workflow file. Use the WP MCP for ad-hoc queries in a session
- So local node buys syntax and logic checking, not a full sync. The authoritative test of a
  JS change is still the Action run

## Planned (Not Yet Done)
- Branch-protection PR workflow on main (Pierre's account would bypass, Claude's token wouldn't)
