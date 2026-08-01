# Keywords

**Read this before touching `tags` in any `media/data/**/*.json`.**

`tags.keywords` is an **open** vocabulary, derived from the data rather than declared —
unlike badges and access, which are closed. Open means it drifts.

## Authoring

Singular and plural are the same word — pick one. Synonyms are the same word — pick one.
These are loose rules applied by a human, not enforced anywhere.

## Never normalize in the filter

No stemming, no synonym maps, no case folding beyond what already exists. Normalizing in
the filter would hide exactly the drift the validation pass exists to expose — two spellings
would silently behave as one, and nothing would ever surface them.

## After keyword work, remind Pierre to run the pass

The pass in [docs/skills/keyword-validation.md](../skills/keyword-validation.md) walks every
`tags.keywords` value across the datasets and surfaces suspects: near-duplicates,
plural/singular pairs, values used only once. **It reports; a human decides.** It is run on
demand — never in the build, never in the filter.

Claude does not run it unprompted, but after any session that adds or edits keywords, say
that it's worth running. Pierre owns the vocabulary decisions.

## Type keywords are load-bearing

`lake` / `park` / `rec-site` / `campground` look redundant to the pass and are not. Nothing
else on a row states the destination type — for per-page rows it's implied by the folder,
for inline dataset rows by nothing at all. Drop them and lakes become unselectable. Whether
type deserves a structured facet of its own is an open question — `docs/todo.md` item 5.
