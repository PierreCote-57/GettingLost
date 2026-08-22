# Keyword validation pass

**Follow this when Pierre says "run a keyword validation pass"**, or asks about keyword
drift, duplicate or near-duplicate keywords, or the keyword vocabulary generally. It
surfaces vocabulary drift — the same word in two forms, odd spellings, collisions with the
badge vocabulary, synonyms — for him to rule on.

`tags.keywords` is an **open** vocabulary — unlike badges and access, nothing
constrains it, so it drifts as pages are authored. This pass surfaces the drift.
It **reports**; Pierre decides. Nothing is edited without him saying so.

Authoring rules the vocabulary is held to: **keywords are written capitalised** (`Visited`,
not `visited`) — they are display text, ruled 2026-08-18; singular/plural are the same word,
pick one; synonyms are the same word, pick one. The lowercase values already in the data are
test content and carry no ruling. Full conventions:
[docs/conventions/keywords.md](../conventions/keywords.md).

## The division of labour

The script does what has an exact rule. You do what needs to know what a word
means. Do not hand the script a language problem because it looks like a string
problem.

**Script** (`local/tools/keyword_validation.py`) — the index, the counts,
case/separator normalization, one legible stemmer for regular number and
conjugation forms, membership tests against the closed badge vocabulary,
co-occurrence.

**You** — everything semantic. Synonyms with no shared spelling (`trout` /
`fishing`), irregular forms the stemmer cannot reach (`goose` / `geese`,
`child` / `children`), and words whose meaning differs despite looking related
(`whale` vs `whaling`). Read the full vocabulary every run; that reading IS the
detector for this half.

Neither side suppresses a finding for being uninteresting. Surfacing is your
job, disposition is Pierre's.

## Step 1 — the report

```bash
python3 local/tools/keyword_validation.py
```

Merge your semantic findings into the script's output as **one flat list**.
Pierre sees one report, not two to reconcile.

```
7 keywords over 6 rows

1. hike (1), hiking (1) --- hiking is also a badge
2. picnic (1) --- is also a badge
3. whale (1), whales (1), whaling (1)
```

Format, all of it settled by Pierre:

- **One line per issue**, one set of words per line, occurrence count in parens.
- **No section headings.** The reason is visible from the line; headings only
  break the sort, and then a keyword's whereabouts depends on why it was flagged.
- **Sorted alphabetically** by the leading word.
- **Leader first** = your guess at the keyword to keep, so `#5: fix` is a
  complete instruction.
- **Numbers as plain text, never a markdown list** — they get cited in a reply,
  and markdown resequences them.
- **Findings sharing a keyword are one line**, reasons joined. Two findings
  touching the same word are one decision; answered apart, the answers can
  contradict.
- Nothing else in the message. "Run a keyword validation pass" means the result,
  not the result wrapped in paragraphs. Do not explain that you did what was asked.

## Step 2 — his questions

Answered off the same index, no re-walk:

```bash
python3 local/tools/keyword_validation.py --vocab        # every keyword + count
python3 local/tools/keyword_validation.py --where WORD   # rows carrying WORD
python3 local/tools/keyword_validation.py --under N      # used fewer than N times
python3 local/tools/keyword_validation.py --row NAME     # keywords on one row
python3 local/tools/keyword_validation.py --with WORD    # co-occurring keywords
```

Count thresholds live here, never in step 1: on a vocabulary still being filled
in, a low count means the keyword is new, not wrong.

## Step 3 — the fix

**The default is nothing.** Pierre names the scope: all of them, one group, or
he does it himself. Finishing one group is not permission to start the next.

For an approved group, replace every non-leader member with the leader across
exactly the rows the index recorded, writing through `local/tools/jsonio.py`.

Trap to honour: a row carrying both `whale` and `whales` collapses to `whale`
twice — de-dupe within the row or the fix creates a new defect.

Re-run afterwards; the group should be gone. That is the verification.

## Rulings carry forward

A settled finding must not come back next run. Two scopes:

- **Local** — this finding, dropped. "trout is fine", "don't show me 4 anymore".
- **Global** — a rule about what counts as a finding at all, applying
  everywhere. "same signal at finer grain is valid."

Recorded below as they are made. They are Pierre's rulings; do not re-litigate
them, and do not re-surface a finding they cover.

### Settled

- **Global — a finer-grained keyword beside a coarser badge is valid, not
  redundant.** `trout` next to the `fishing` badge is deliberate: in fishing the
  target species changes everything, so the species is not a finer label for the
  same signal. Do not flag species-vs-activity overlap (2026-07-30).
- **Global — type words are no longer keywords at all** (2026-08-01). `lake` /
  `park` / `rec-site` / `campground` moved to their own closed facet,
  `tags.types` ([docs/schema/types.md](../schema/types.md)), so the walk no
  longer sees them and the old "load-bearing, do not flag" ruling they needed
  (2026-07-30) is retired. If one turns up in `tags.keywords` again, that IS a
  finding: it belongs in `types`.

## Scope of the walk

Files under `media/` where `tags.keywords` is applicable to the site. Not
`local/data/` — those are unauthored source datasets.

The walk finds any object carrying `tags.keywords` at any depth, which is what
picks up the inline rows inside dataset files. A per-page glob misses those, and
they are where most of the tagging lives — `whales` existed only there.
