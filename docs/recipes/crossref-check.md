# The cross-reference validation pass

```
python3 local/tools/crossref_check.py
python3 local/tools/crossref_check.py --verbose
```

`local/tools/crossref_check.py` checks the link graph between pages: that every pointer
lands, and that the two sides agree on the target's name. It reports and never edits. Exit
code is 1 when anything is found, 0 when clean.

Run it after changing destination content — a page rename, a new notes section naming
neighbours, a dataset row gaining or losing a `file`. Nothing at build time catches a link
that stopped landing; the page fetches its JSON at runtime, so the failure shows up as a
console error on a visitor's screen.

## The three checks

| Check | What it proves |
| --- | --- |
| `target` | every `file` link resolves to exactly one file — a page under `pages/`, a dataset under `media/data/` |
| `data` | an `.html` target has its matching `.json`, the one the page fetches at runtime |
| `name` | the link's own `name` matches the `name` in the target's JSON |

The `name` check needs both sides to have one. It is skipped for a link with no `name`, and
for a target whose JSON has none — the list-browser catalog rows are the case, labelling a
dataset with `title`, which is the catalog's display word rather than a claim about anything
inside the target.

## Scope of the walk

JSON under `media/`. Any object carrying a string `file` at any depth is a link, which is
what picks up the rows inline in dataset files — a per-page glob would miss those, and they
are where most of the links live. `local/data/` is out of scope: unauthored source datasets.

Links are resolved **by filename**, never by path, because that is how authors write them
(`"file": "sproat-lake-provincial-park.html"`). A filename that resolves to two files is
itself a finding — the slug model requires it to be unique.

## Out of scope, both ruled 2026-08-10

- **Reciprocity.** A one-way link is correct, not a defect. A lake has reason to name the
  park at its shore, and the park may have nothing to say about the lake.
- **Prose.** Whether the two sides' `description` still tell the same story is a reading job,
  not a rule, and the script does not pretend to it.

Related: [doc-validation.md](doc-validation.md) — the same shape for the markdown,
[../conventions/site.md](../conventions/site.md) for the convention this enforces,
[../schema/links.md](../schema/links.md) for `file` vs `url`.
