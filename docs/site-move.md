# When the site leaves wpcomstaging.com

Things that are correct today only because the site still lives at
`gettinglostonvi.wpcomstaging.com`, and that have to be dealt with when it moves to the
production domain. Not work to do now — a list to walk at that moment.

**This is not parked work and never belongs in a "where are we?" answer.** It has no owner
and no date; it is triggered by the move. Parked work is `docs/todo.md`.

## Lock the Google Maps API key to the production domain

The key is declared in `media/data/scripts/gl-constants.jst` as `MAP_CONFIG.mapApiKey` and
used by the `googleMap` renderer in `gettinglost.jst`. Its HTTP-referrer restriction lives in
the Google Cloud console, on the credentials page for the key.

**It IS restricted, to the staging site** (confirmed by Pierre against the console,
2026-08-01). So this is not a tidy-up at the move — **every map on the site breaks the moment
the domain changes**, until the allow-list has the new domain on it. Add the production
domain before or with the cutover, and remove the staging host once nothing serves from it.

## Update the hardcoded hostname

`gettinglostonvi.wpcomstaging.com` is written into these, and each has to be revisited:

- [../README.md](../README.md) — the site link in the opening paragraph
- [toolchain.md](toolchain.md) — the session-start WordPress MCP check and the live-site
  inspection notes
- [overview.md](overview.md) — the site identity line
- [rendering/wp-templates.md](rendering/wp-templates.md) — site host and blog_id
- [reference/filebird-api.md](reference/filebird-api.md) — the folders endpoint URL

`schema/image.md` and `schema/wp-title-date.md` also name the host, but only in dated prose
about how something was learned — nothing to change there.

The blog_id (`255518505`) does not change with the domain.
