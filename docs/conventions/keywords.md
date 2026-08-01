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

## Type is NOT a keyword any more

`lake` / `park` / `rec-site` / `campground` used to be keywords, and load-bearing ones —
nothing else on a row said what kind of place it was. They became their own closed facet,
`tags.types`, on 2026-08-01; see [docs/schema/types.md](../schema/types.md). Do not
reintroduce them here: a word that says what a place IS belongs to that vocabulary, where it
can be validated and counted.
