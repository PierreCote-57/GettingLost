# The documentation validation pass

```
python3 local/tools/check_docs.py
python3 local/tools/check_docs.py --verbose
```

`local/tools/check_docs.py` checks what a script can check about `docs/`: that every
pointer resolves and every name still exists. It reports and never edits. Exit code is 1
when anything is found, 0 when clean.

Run it after any session that moved files, renamed something in the code, or changed a
folder tree — and as the last step of a docs cleanup, so the mechanical half is settled
before anyone reads prose.

## The five checks

| Check | What it proves |
| --- | --- |
| `links` | every relative markdown link resolves to a file that exists |
| `paths` | every backticked `media/…`, `pages/…`, `local/…` path exists on disk |
| `index` | `docs/README.md` lists every doc; `docs/projects/README.md` every project |
| `tree` | the folder tree in `conventions/folders.md` matches `media/data` and `pages` |
| `names` | a symbol a doc attributes to one of our source files still exists |

## What it does NOT check

**Prose.** Whether a paragraph still describes how the site works is a reading job, and no
script does it. The pass settles the part that rots silently — a link to a renamed file, a
path that moved, a tree that drifted — so the reading can be about meaning.

## Two conventions the checks depend on

**`← WP only` in the folders.md tree.** A folder that lives in WordPress with no repo
counterpart is annotated that way and the tree check skips it. `shared/gallery/` is the
case: sync writes the generated `PageMap.json` there, and nothing in the repo mirrors it.
Without the annotation it reads as drift on every run.

**A retirement word keeps a line out of the `names` check** — retired, removed, deleted,
obsolete, gone, dropped, no longer, was, replaced. A doc naming `GALLERY_RULES` to say it
is deleted is the docs doing their job, not rot, and flagging those buries the real ones.

## Why `names` is scoped the way it is

The first draft checked every code-shaped backticked token against the whole source tree
and reported 88 findings, of which about six were real. WP field names, FileBird
parameters and BC dataset columns all read as code and none of them are ours.

Three rules fixed it, and they are worth keeping if the check is ever extended:

1. **A filename has to sit within 40 characters of the symbol.** "gettinglost.jst
   `renderPhoto()`" is a claim about this repo; a filename further down the same sentence
   is talking about something else.
2. **A retirement word on the line skips it** (above).
3. **The symbol must be absent from every source file, not just the named one.** A symbol
   that merely moved between our files is a misattribution, not rot.

The tuned version found one finding, and it was real: `renderPhoto()`, which the code has
called `blockRenderers.photo` for some time.

Related: [../conventions/folders.md](../conventions/folders.md),
[../skills/keyword-validation.md](../skills/keyword-validation.md) — the same
report-never-edit shape, for the keyword vocabulary.
