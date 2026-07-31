#!/usr/bin/env python3
"""Keyword validation pass — the mechanical half.

Builds the keyword index from the authored JSON under media/, then runs the
detectors that have a deterministic rule. It REPORTS; it never edits, and it
never suppresses a finding for being uninteresting.

What lives here is everything a script is actually good at: exact comparisons,
lookups and counting. Anything that needs to know what a word MEANS — trout vs
fishing, goose vs geese — is not here on purpose. English morphology is
irregular, so one legible stemmer runs as an exhaustive net for the regular
cases and the reading of the vocabulary happens outside this script.

Usage:

    keyword_validation.py                 the step-1 report
    keyword_validation.py --vocab         every keyword with its count
    keyword_validation.py --where WORD    the rows carrying WORD
    keyword_validation.py --under N       keywords used fewer than N times
    keyword_validation.py --row NAME      the keywords carried by a row
    keyword_validation.py --with WORD     keywords co-occurring with WORD

The step-2 queries all read the same index the report is built from, so none of
them re-walks the tree.
"""

import collections
import json
import os
import sys

MEDIA_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "media")

# Suffixes stripped to reach a stem, longest first so -ies wins over -es/-s.
# Deliberately short: every rule here is one a reader can check by eye.
SUFFIX_RULES = [("ies", "y"), ("ing", ""), ("ed", ""), ("es", ""), ("er", ""), ("s", "")]

MIN_STEM = 3


# Every JSON file under media/, sorted so a run is reproducible.
def findJsonFiles(mediaRoot):
	jsonPaths = []
	for dirPath, dirNames, fileNames in os.walk(mediaRoot):
		dirNames.sort()
		for fileName in sorted(fileNames):
			if fileName.endswith(".json"):
				jsonPaths.append(os.path.join(dirPath, fileName))
	return jsonPaths


# Walk any JSON structure and yield each object carrying tags.keywords. A page
# file is one such object; a dataset file is a list of them (the inline rows a
# per-page glob never sees), so both are found without special-casing either.
def findTaggedRows(node):
	taggedRows = []
	if isinstance(node, dict):
		tags = node.get("tags")
		if isinstance(tags, dict) and isinstance(tags.get("keywords"), list):
			taggedRows.append(node)
		for value in node.values():
			taggedRows.extend(findTaggedRows(value))
	elif isinstance(node, list):
		for value in node:
			taggedRows.extend(findTaggedRows(value))
	return taggedRows


# What to call a row in a report. A dataset file holds many rows, so the file
# name alone cannot answer "where does this show up".
def rowLabel(row):
	label = row.get("name") or row.get("title") or row.get("file") or "(unnamed)"
	return label


# The index: keyword -> [{file, row}], plus the per-row keyword lists and the
# structured vocabularies the collision detector tests against.
def buildIndex(mediaRoot):
	occurrences = collections.defaultdict(list)
	rowKeywords = []
	badgeValues = set()
	datasetSizes = collections.Counter()

	for jsonPath in findJsonFiles(mediaRoot):
		with open(jsonPath, encoding="utf-8") as handle:
			try:
				data = json.load(handle)
			except json.JSONDecodeError:
				print(f"SKIPPED (not parseable): {jsonPath}", file=sys.stderr)
				continue
		relPath = os.path.relpath(jsonPath, mediaRoot)
		for row in findTaggedRows(data):
			label = rowLabel(row)
			keywords = row["tags"]["keywords"]
			rowKeywords.append({"file": relPath, "row": label, "keywords": keywords})
			datasetSizes[relPath] += 1
			for badge in row["tags"].get("badges") or []:
				badgeValues.add(badge)
			for keyword in keywords:
				occurrences[keyword].append({"file": relPath, "row": label})

	index = {
		"occurrences": dict(occurrences),
		"rowKeywords": rowKeywords,
		"badgeValues": badgeValues,
		"datasetSizes": datasetSizes,
	}
	return index


# Lowercase, letters and digits only — so rec-site, Rec Site and recsite all
# collapse onto one key and show up as spellings of the same word.
def normalizeKey(keyword):
	key = "".join(character for character in keyword.lower() if character.isalnum())
	return key


# Strip one suffix and undouble a final doubled consonant, then drop a trailing
# e so hike and hiking meet at the same key. Regular cases only, by design.
def stemKey(keyword):
	stem = normalizeKey(keyword)
	for suffix, replacement in SUFFIX_RULES:
		if stem.endswith(suffix) and len(stem) - len(suffix) >= MIN_STEM:
			stem = stem[: -len(suffix)] + replacement
			break
	if len(stem) > MIN_STEM and stem[-1] == stem[-2] and stem[-1] not in "aeiou":
		stem = stem[:-1]
	if len(stem) > MIN_STEM and stem.endswith("e"):
		stem = stem[:-1]
	return stem


# The keyword a group should collapse onto if Pierre agrees: lowercase first
# (it is the rule), then most used, then shortest. A guess, not a verdict.
def guessLeader(members, counts):
	leader = sorted(members, key=lambda word: (word != word.lower(), -counts[word], len(word), word))[0]
	return leader


# Groups of keywords that are spellings or forms of one word, keyed first by
# normalization (case and separators) then by stem (number and conjugation).
def findFormGroups(counts):
	groups = []
	for keyFunction in (normalizeKey, stemKey):
		buckets = collections.defaultdict(set)
		for keyword in counts:
			buckets[keyFunction(keyword)].add(keyword)
		for members in buckets.values():
			if len(members) > 1 and members not in [group["members"] for group in groups]:
				groups.append({"members": members, "leader": guessLeader(members, counts)})
	merged = mergeOverlapping(groups, counts)
	return merged


# Fold groups sharing a member into one, so a word does not get reported twice
# under two different keys.
def mergeOverlapping(shortList, counts):
	merged = []
	for group in shortList:
		hit = None
		for existing in merged:
			if existing["members"] & group["members"]:
				hit = existing
				break
		if hit:
			hit["members"] = hit["members"] | group["members"]
			hit["leader"] = guessLeader(hit["members"], counts)
		else:
			merged.append({"members": set(group["members"]), "leader": group["leader"]})
	return merged


# Keywords that repeat a value the row already carries in a structured field.
def findStructuredCollisions(counts, badgeValues):
	collisions = []
	for keyword in sorted(counts):
		if keyword in badgeValues:
			collisions.append({"keyword": keyword, "reason": "is also a badge"})
	return collisions


# Keywords carried by every row of a file — the option that never narrows.
def findUniversal(index, counts):
	universal = []
	perFile = collections.defaultdict(collections.Counter)
	for entry in index["rowKeywords"]:
		for keyword in entry["keywords"]:
			perFile[entry["file"]][keyword] += 1
	for filePath, keywordCounts in sorted(perFile.items()):
		size = index["datasetSizes"][filePath]
		if size < 2:
			continue
		for keyword, count in sorted(keywordCounts.items()):
			if count == size:
				universal.append({"keyword": keyword, "reason": f"on every row of {filePath} ({size})"})
	return universal


def countKeywords(index):
	counts = collections.Counter()
	for keyword, rows in index["occurrences"].items():
		counts[keyword] = len(rows)
	return counts


# Fold findings that share a keyword into one, keeping every reason. Two
# findings touching the same word are one decision, not two: answering them
# apart lets the answers contradict each other, and collapsing a form group can
# silently invalidate a collision reported on the member that disappears.
def mergeSharedFindings(longList, counts):
	merged = []
	for finding in longList:
		hit = None
		for existing in merged:
			if existing["members"] & finding["members"]:
				hit = existing
				break
		if hit:
			hit["members"] = hit["members"] | finding["members"]
			hit["reasons"] = hit["reasons"] + finding["reasons"]
			hit["leader"] = guessLeader(hit["members"], counts)
		else:
			merged.append(dict(finding, members=set(finding["members"])))
	return merged


# Every finding as one {leader, members, reasons} record, so the report can be a
# single flat list. Sections would break the alphabetical order and put one
# keyword in two places depending on why it was flagged.
def collectFindings(index, counts):
	findings = []
	for group in findFormGroups(counts):
		findings.append({"leader": group["leader"], "members": group["members"], "reasons": []})
	for item in findStructuredCollisions(counts, index["badgeValues"]):
		findings.append({"leader": item["keyword"], "members": {item["keyword"]}, "reasons": [item]})
	for item in findUniversal(index, counts):
		findings.append({"leader": item["keyword"], "members": {item["keyword"]}, "reasons": [item]})
	merged = mergeSharedFindings(findings, counts)
	ordered = sorted(merged, key=lambda finding: finding["leader"])
	return ordered


# The text after `---`. A reason names its own keyword only when the line holds
# more than one, so a single-word line does not repeat itself.
def formatReasons(finding):
	parts = []
	for item in finding["reasons"]:
		if len(finding["members"]) > 1:
			parts.append(f"{item['keyword']} {item['reason']}")
		else:
			parts.append(item["reason"])
	text = "; ".join(parts)
	return text


# The step-1 report: one flat alphabetical list, each line carrying its own
# reason. Numbers are plain text on purpose — they are cited in a reply, and a
# markdown list would resequence them.
def printReport(index):
	counts = countKeywords(index)
	findings = collectFindings(index, counts)

	rowCount = len(index["rowKeywords"])
	print(f"{len(counts)} keywords over {rowCount} rows\n")

	if not findings:
		print("(nothing flagged)")
	for number, finding in enumerate(findings, start=1):
		others = sorted(member for member in finding["members"] if member != finding["leader"])
		ordered = [finding["leader"]] + others
		listed = ", ".join(f"{member} ({counts[member]})" for member in ordered)
		reasons = formatReasons(finding)
		suffix = f" --- {reasons}" if reasons else ""
		print(f"{number}. {listed}{suffix}")


def printVocab(index):
	counts = countKeywords(index)
	for keyword in sorted(counts):
		print(f"{counts[keyword]:4d}  {keyword}")


def printWhere(index, keyword):
	for entry in index["occurrences"].get(keyword, []):
		print(f"{entry['row']}  --  {entry['file']}")


def printUnder(index, threshold):
	counts = countKeywords(index)
	for keyword in sorted(counts):
		if counts[keyword] < threshold:
			print(f"{counts[keyword]:4d}  {keyword}")


def printRow(index, name):
	for entry in index["rowKeywords"]:
		if entry["row"].lower() == name.lower():
			print(f"{entry['row']}  --  {entry['file']}")
			print("  " + ", ".join(sorted(entry["keywords"])))


# Keywords sharing a row with the given one, most shared first — the handle on
# synonyms, which nothing in this script can detect on its own.
def printWith(index, keyword):
	together = collections.Counter()
	for entry in index["rowKeywords"]:
		if keyword in entry["keywords"]:
			for other in entry["keywords"]:
				if other != keyword:
					together[other] += 1
	for other, count in together.most_common():
		print(f"{count:4d}  {other}")


def main(argv):
	index = buildIndex(MEDIA_ROOT)
	if not argv:
		printReport(index)
	elif argv[0] == "--vocab":
		printVocab(index)
	elif argv[0] == "--where":
		printWhere(index, argv[1])
	elif argv[0] == "--under":
		printUnder(index, int(argv[1]))
	elif argv[0] == "--row":
		printRow(index, argv[1])
	elif argv[0] == "--with":
		printWith(index, argv[1])
	else:
		print(__doc__)
		return 1
	return 0


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
