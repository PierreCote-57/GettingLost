# When the site leaves wpcomstaging.com

Things that are correct today only because the site still lives at
`gettinglostonvi.wpcomstaging.com`, and that have to be dealt with when it moves to the
production domain. Not work to do now — a list to walk at that moment.

**This is not parked work and never belongs in a "where are we?" answer.** It has no owner
and no date; it is triggered by the move. Parked work is `docs/todo.md`.

## Lock the Google Maps API key to the production domain

The key is loaded in `media/data/scripts/gettinglost.jst` as `MAP_CONFIG.mapApiKey`. Its
HTTP-referrer restriction lives in the Google Cloud console, on the credentials page for the
key — nothing in the repo records it. Set the allow-list to the new domain as part of the
move, and remove the staging host once nothing serves from it.

## Update the hardcoded hostname

`gettinglostonvi.wpcomstaging.com` is written into these, and each has to be revisited:

- [toolchain.md](toolchain.md) — the session-start WordPress MCP check and the live-site
  inspection notes
- [overview.md](overview.md) — the site identity line
- [rendering/wp-templates.md](rendering/wp-templates.md) — site host and blog_id
- [reference/filebird-api.md](reference/filebird-api.md) — the folders endpoint URL

The blog_id (`255518505`) does not change with the domain.
