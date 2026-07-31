# Rec-site suggestions API

Endpoint to look up a Recreation Site by name:

`https://dj2qs6gf0wkg3.cloudfront.net/api/v1/recreation-resource/suggestions?query=<q>`

- The `query` is a **"contains" (substring)** match: `query=a` returns both `abc` and `bac` — anything containing the letter.
- **Use only the first letter** of the name you're after (e.g. `query=l` to find "Leiner River") — a short contains-query gives the widest net and best chance of a hit despite spelling/naming variation; then filter the returned list yourself.

Pierre supplied this 2026-07-19 as the go-to way to resolve an RSTBC rec-site (name → resource, which pairs with the `sitesandtrailsbc.ca/resource/REC####` page pattern). Relevant to the destinations-overview data passes — see [docs/recipes/data-fill.md](../recipes/data-fill.md), [docs/projects/destinations-overview.md](../projects/destinations-overview.md), [docs/recipes/lake-page.md](../recipes/lake-page.md).
