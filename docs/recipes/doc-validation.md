# The documentation validation pass

```
python3 local/tools/check_docs.py
python3 local/tools/check_docs.py --verbose   # adds a one-line count of what was walked
```

`local/tools/check_docs.py` checks what a script can check about the markdown Claude
maintains: that every pointer resolves and every name still exists. It reports and never
edits. Exit code is 1 when anything is found, 0 when clean.

Run it after any session that moved files or renamed something in the code — and as the
last step of a docs cleanup, so the mechanical half is settled before anyone reads prose.

## The six checks

| Check | What it proves |
| --- | --- |
| `links` | every relative markdown link resolves to a file that exists |
| `paths` | every backticked `media/…`, `pages/…`, `local/…` or `~/…` path exists on disk |
| `index` | `docs/README.md` lists every doc; `docs/projects/README.md` every project |
| `names` | a symbol a doc attributes to one of our source files still exists |
| `cache` | no doc states a count of what the data holds right now |
| `format` | every `media/data` JSON round-trips byte-identically through `jsonio` |

## Three sets of files

| Set | Checked |
| --- | --- |
| `docs/` | everything |
| the repo root — `CLAUDE.md`, `README.md` | everything but the index |
| `~/Claude/` | links and `~/…` paths only |

**`~/Claude/` is narrow on purpose.** Those files load in EVERY project, so a bare
`docs/todo.md` in one of them means "the current project's", not this repo's — checking it
here would assert something the file never claimed. Their code names are not checked against
this repo's source for the same reason.

The repo root was outside the walk until 2026-08-09, and that is exactly where the drift
hid: the root `README.md` had a stale `pages/van/` tree, a `local/tools/` listing missing a
file, `.claude/` described as holding notes it no longer holds, and a sync paragraph that
omitted `.pdf`. Nothing else was checking it.

## What it does NOT check

**Prose.** Whether a paragraph still describes how the site works is a reading job, and no
script does it. The pass settles the part that rots silently — a link to a renamed file, a
path that moved, a symbol the code no longer has — so the reading can be about meaning.

**A symbol unbound from a filename.** A broad "does this exist anywhere in our source"
scan was added and removed the same day (2026-08-21): 29 findings, every one a false
positive — Claude tool names, LakeData columns, PIL classes, keyword *values*, and symbols
the docs name precisely in order to say they were rejected or retired. It fails for the same
reason `names` is scoped the way it is, below, and the exclusion list it would need is just
another cache. Reading catches these; a script does not.

**Anything the repo already holds.** A `tree` check comparing a folder tree in
`conventions/folders.md` against the disk was deleted 2026-08-21 along with the tree itself.
It could only ever detect that the copy had drifted, which is a problem the copy created, and
it went red on ordinary work — every page added. The trees are gone; see
[../README.md](../README.md), "These files are not a cache of the repo".

## Two conventions the checks depend on

**A retirement word keeps a line out of the `names` AND `paths` checks** — retired, removed,
deleted, obsolete, dead, gone, dropped, died, no longer, was, old, used to, replaced, renamed
from, not moved, does not exist, never existed (`RETIREMENT_WORDS` in the script). A doc
naming `GALLERY_RULES` to say it is deleted is the docs doing their job, not rot, and
flagging those buries the real ones.

**A placeholder is never checked** — anything carrying `<`, `>`, `{`, `}`, `*` or an
ellipsis. That is why the site's naming convention matters in prose too: write
`pages/<name>.html`, since a made-up `foo.html` under a real folder sends the checker
looking for a file nobody meant to exist. It also keeps the docs saying `<name>` where the
filename is master, rather than `<slug>`, which is derived.

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

Related: [crossref-check.md](crossref-check.md) and
[../skills/keyword-validation.md](../skills/keyword-validation.md) — the same
report-never-edit shape, for the link graph and the keyword vocabulary.
