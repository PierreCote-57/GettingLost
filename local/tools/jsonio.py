#!/usr/bin/env python3
"""Read/write repo JSON in the house format, from one place.

Every data pass that rewrites a JSON file under media/data/ or logs/ should go
through save() here rather than calling json.dump directly, so the formatting
can't drift between scripts (tabs vs spaces, escaped vs literal accents, a
missing trailing newline). Import it from a sibling script:

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
    from jsonio import load, save

    data = load(path)
    ...mutate data...
    save(path, data)

House format (matches what IntelliJ produces on "reformat", so Pierre's editor
and these scripts agree and never fight over the file):

  - TAB indentation, one field per line. Verbose on purpose: a one-field change
    is a one-line git diff, and IntelliJ can collapse/expand records.
  - ensure_ascii=False, so en dashes and accents stay literal instead of
    turning into \\u2013 escapes.
  - Trailing newline.

NOTE: local/data/ is deliberately out of scope. Those files are historical
reference material captured in whatever format suited them at the time; they
are read-only unless Pierre specifically asks for a change. Do not point save()
at them.
"""

import json

INDENT = "\t"


def load(path):
    """Parse a JSON file (UTF-8)."""
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def dumps(data):
    """Serialize to the house format, without the trailing newline."""
    return json.dumps(data, ensure_ascii=False, indent=INDENT)


def save(path, data):
    """Write a JSON file in the house format, overwriting it."""
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(dumps(data))
        handle.write("\n")
