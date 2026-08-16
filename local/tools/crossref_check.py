#!/usr/bin/env python3
"""Cross-reference validation pass — the link graph only.

Pages point at each other by FILENAME: a lake's notes name a nearby park, a
list-browser catalog names its dataset. Nothing at build time checks that those
pointers still land, so a renamed file leaves a link that fetches a 404 at
runtime and no one hears about it. This walks every one of them.

It REPORTS; it never edits, and it never drops a finding for being
uninteresting. Exit code is 1 when anything is found, 0 when clean.

    crossref_check.py                 the report
    crossref_check.py --verbose       also list every link it walked

Five checks:

    target    the linked file exists, and the name resolves to exactly one file
    data      an .html target has its matching .json beside it
    name      the link's own `name` matches the `name` in the target's JSON
    location  a `location` is concrete lat/lng and never holds a pointer
    registry  every `location_id` resolves to a record in logs/locations.json

The last two guard the map model ([docs/schema/map-pins-location.md]): a named
`googleMap` entry may point at a page (`file`) or a registry record
(`location_id`), and what it lands on is a `location`. A `location` that pointed
somewhere itself would make resolution a chain instead of one hop, so the rule
is that it never does — which is what makes a pointer always terminate. A `file`
pointer needs no rule of its own here: it is an object carrying a string `file`,
so the target and data checks above already walk it.

Out of scope on purpose:

  - RECIPROCITY. A one-way link is correct, not a defect: a lake has reason to
    name the park at its shore, and the park may have nothing to say about the
    lake (ruled 2026-08-10).
  - PROSE. Whether the two sides' `description` still tell the same story is a
    reading job, not a rule (ruled 2026-08-10).

Scope of the walk: JSON under media/, plus logs/locations.json for the two map
checks — the registry defines the records `location_id` names, so it has to be
read to say whether one lands, and its own records carry a `location`.
Any object carrying a string `file` at any depth is a link, which is what picks
up the rows inline in dataset files — a per-page glob would miss them, and that
is where most of the links live. `local/data/` is out of scope; those are
unauthored source datasets.

The `name` check is skipped for a link that carries no `name`, and for one whose
target JSON has none. The list-browser catalog rows are the case: they label a
dataset with `title`, which is the catalog's own display word and not a claim
about anything inside the target.
"""

import json
import os
import sys

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
MEDIA_DATA = os.path.join(REPO_ROOT, "media", "data")
PAGES_ROOT = os.path.join(REPO_ROOT, "pages")


# Repo-relative, so a finding can be pasted straight into a message.
def relative(path):
	relPath = os.path.relpath(path, REPO_ROOT)
	return relPath


# Every file under a root, indexed by bare filename — authors reference other
# pages by filename alone, so the folder layout cannot take part in resolution.
# A filename mapping to more than one path is itself a finding; the list is kept
# whole rather than collapsed so the target check can say so.
def indexByFilename(root, extension):
	index = {}
	for dirPath, dirNames, fileNames in os.walk(root):
		dirNames.sort()
		for fileName in sorted(fileNames):
			if fileName.endswith(extension):
				index.setdefault(fileName, []).append(os.path.join(dirPath, fileName))
	return index


# Every JSON file under media/, sorted so a run is reproducible.
def findDataFiles(root):
	dataPaths = []
	for dirPath, dirNames, fileNames in os.walk(root):
		dirNames.sort()
		for fileName in sorted(fileNames):
			if fileName.endswith(".json"):
				dataPaths.append(os.path.join(dirPath, fileName))
	return dataPaths


# Every link in one JSON file: an object with a string `file`, wherever it sits.
# The path through the document travels with it so a finding can say which row
# it came from, and the object's own `name` so the name check has both sides.
def collectLinks(dataPath):
	with open(dataPath, encoding="utf-8") as handle:
		data = json.load(handle)

	links = []

	def walk(node, where):
		if isinstance(node, dict):
			target = node.get("file")
			if isinstance(target, str):
				links.append({"source": dataPath, "where": where or "/", "file": target,
					"name": node.get("name")})
			for key in node:
				walk(node[key], where + "/" + key)
		elif isinstance(node, list):
			for index, item in enumerate(node):
				walk(item, "%s[%d]" % (where, index))

	walk(data, "")
	return links


# Every link across every data file, in file order.
def collectAllLinks(dataPaths):
	allLinks = []
	for dataPath in dataPaths:
		allLinks.extend(collectLinks(dataPath))
	return allLinks


# Where a link's filename resolves, by extension: a page under pages/, a dataset
# under media/data/. An unknown extension resolves nowhere and the target check
# reports it — the two the site uses are all the site has.
def resolveTarget(fileName, pageIndex, dataIndex):
	if fileName.endswith(".html"):
		matches = pageIndex.get(fileName, [])
		return matches
	if fileName.endswith(".json"):
		matches = dataIndex.get(fileName, [])
		return matches
	return []


# CHECK: every link resolves to exactly one file.
def checkTargets(links, pageIndex, dataIndex):
	findings = []
	for link in links:
		matches = resolveTarget(link["file"], pageIndex, dataIndex)
		if not matches:
			findings.append("%s %s: `%s` does not resolve" %
				(relative(link["source"]), link["where"], link["file"]))
		elif len(matches) > 1:
			where = ", ".join(relative(match) for match in matches)
			findings.append("%s %s: `%s` resolves to %d files — %s" %
				(relative(link["source"]), link["where"], link["file"], len(matches), where))
	return findings


# The JSON a page fetches at runtime: the same base, `.json` for `.html`, in the
# page's own data folder. Resolution is by filename, same as the page itself.
def targetDataPath(fileName, pageIndex, dataIndex):
	if not fileName.endswith(".html"):
		matches = resolveTarget(fileName, pageIndex, dataIndex)
		return matches[0] if len(matches) == 1 else None
	dataName = os.path.splitext(fileName)[0] + ".json"
	matches = dataIndex.get(dataName, [])
	return matches[0] if len(matches) == 1 else None


# CHECK: an .html target has its matching .json. A page fetches its JSON at
# runtime, so a missing one is a console error on a page we linked to.
def checkData(links, pageIndex, dataIndex):
	findings = []
	seen = set()
	for link in links:
		fileName = link["file"]
		if not fileName.endswith(".html"):
			continue
		if not resolveTarget(fileName, pageIndex, dataIndex):
			continue                    # unresolved target — already a finding
		dataName = os.path.splitext(fileName)[0] + ".json"
		if dataName in seen:
			continue
		seen.add(dataName)
		if not dataIndex.get(dataName):
			findings.append("%s %s: `%s` exists but its `%s` does not" %
				(relative(link["source"]), link["where"], fileName, dataName))
	return findings


# CHECK: the link's `name` matches the `name` the target's own JSON carries.
# Both sides have to have one — see the module docstring on catalog rows.
def checkNames(links, pageIndex, dataIndex):
	findings = []
	for link in links:
		if not link["name"]:
			continue
		dataPath = targetDataPath(link["file"], pageIndex, dataIndex)
		if dataPath is None:
			continue                    # unresolved or ambiguous — already a finding
		with open(dataPath, encoding="utf-8") as handle:
			targetData = json.load(handle)
		targetName = targetData.get("name")
		if not targetName:
			continue
		if targetName != link["name"]:
			findings.append("%s %s: link says \"%s\", %s says \"%s\"" %
				(relative(link["source"]), link["where"], link["name"],
					relative(dataPath), targetName))
	return findings


# Every `location` block in one JSON document, with the path that reached it, so
# a finding can name the row it came from. Registry files are a list of records,
# page files a single object; both are walked the same way.
def collectLocations(document, source, where="", found=None):
	locations = [] if found is None else found
	if isinstance(document, dict):
		for key, value in document.items():
			path = where + "." + key
			if key == "location" and isinstance(value, dict):
				locations.append({"source": source, "where": path, "location": value})
			else:
				collectLocations(value, source, path, locations)
	elif isinstance(document, list):
		for index, value in enumerate(document):
			collectLocations(value, source, "%s[%d]" % (where, index), locations)
	return locations


# Every `location_id` in one JSON document, with the path that reached it.
def collectLocationIds(document, source, where="", found=None):
	references = [] if found is None else found
	if isinstance(document, dict):
		for key, value in document.items():
			path = where + "." + key
			if key == "location_id" and isinstance(value, str):
				references.append({"source": source, "where": path, "id": value})
			else:
				collectLocationIds(value, source, path, references)
	elif isinstance(document, list):
		for index, value in enumerate(document):
			collectLocationIds(value, source, "%s[%d]" % (where, index), references)
	return references


# CHECK: a `location` is the place itself — concrete coordinates, never a
# pointer. A location that pointed somewhere would turn one-hop resolution into
# a chain, so both halves of that are findings here.
def checkLocations(locations):
	findings = []
	for entry in locations:
		block = entry["location"]
		label = "%s %s" % (relative(entry["source"]), entry["where"])
		for pointer in ("file", "location_id"):
			if pointer in block:
				findings.append("%s holds a %r — a location never points" % (label, pointer))
		for axis in ("lat", "lng"):
			if not isinstance(block.get(axis), (int, float)):
				findings.append("%s has no concrete %r" % (label, axis))
	return findings


# CHECK: every `location_id` names a record that exists. A dangling one is a
# console error and an empty map at runtime.
def checkRegistry(references, registryIds):
	findings = []
	for reference in references:
		if reference["id"] not in registryIds:
			findings.append("%s %s -> %r is not a record in logs/locations.json" %
				(relative(reference["source"]), reference["where"], reference["id"]))
	return findings


# The report: one section per check, numbered as plain text so the numbers
# survive being pasted into a reply.
def printReport(sections):
	total = 0
	for name, findings in sections:
		print("%s — %d" % (name, len(findings)))
		for number, finding in enumerate(findings, start=1):
			print("  %d. %s" % (number, finding))
		total += len(findings)
		print()
	print("%d findings" % total)
	return total


def main(argv):
	verbose = "--verbose" in argv
	pageIndex = indexByFilename(PAGES_ROOT, ".html")
	dataIndex = indexByFilename(MEDIA_DATA, ".json")
	dataPaths = findDataFiles(os.path.join(REPO_ROOT, "media"))
	links = collectAllLinks(dataPaths)

	registryPath = os.path.join(REPO_ROOT, "logs", "locations.json")
	registry = json.load(open(registryPath, encoding="utf-8"))
	registryIds = {record["id"] for record in registry if "id" in record}

	locations = collectLocations(registry, registryPath)
	references = collectLocationIds(registry, registryPath)
	for dataPath in dataPaths:
		document = json.load(open(dataPath, encoding="utf-8"))
		collectLocations(document, dataPath, "", locations)
		collectLocationIds(document, dataPath, "", references)

	if verbose:
		print("%d links in %d data files, against %d pages and %d data files\n" %
			(len(links), len(dataPaths), len(pageIndex), len(dataIndex)))
		for link in links:
			print("  %s %s -> %s" % (relative(link["source"]), link["where"], link["file"]))
		print()

	sections = [
		("target", checkTargets(links, pageIndex, dataIndex)),
		("data", checkData(links, pageIndex, dataIndex)),
		("name", checkNames(links, pageIndex, dataIndex)),
		("location", checkLocations(locations)),
		("registry", checkRegistry(references, registryIds)),
	]
	total = printReport(sections)
	return 1 if total else 0


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
