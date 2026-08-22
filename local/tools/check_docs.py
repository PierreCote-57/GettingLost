#!/usr/bin/env python3
"""Documentation validation pass — the mechanical half.

Checks what a script can check about the markdown Claude maintains: that every
pointer resolves and every name it uses still exists. It REPORTS; it never
edits, and it never drops a finding for being uninteresting.

Prose is out of scope on purpose. Whether a paragraph still describes how the
site works is a reading job, and no script can do it. What lives here is the
part that rots silently: a link to a renamed file, a path that moved, a
function the code no longer has.

    check_docs.py                 the report
    check_docs.py --verbose       also list what each check looked at

Six checks:

    links     every relative markdown link resolves
    paths     every backticked repo or home path exists
    index     docs/README.md lists every doc; projects/README.md every project
    names     every code symbol a doc attributes to a source file still exists
    cache     no doc states a count of what the data holds right now
    format    every media/data JSON round-trips byte-identically through jsonio

A seventh was tried and REMOVED 2026-08-21: a broad "does this symbol exist
anywhere in our source" scan, unbound from a nearby filename. It reported 29
findings and every one was a false positive — Claude tool names, LakeData
columns, PIL classes, keyword VALUES, and symbols the docs name precisely to say
they were rejected or retired. It fails for the same reason `names` is scoped the
way it is (below), and a curated exclusion list would just be another cache. That
check stays a reading job.

Three sets of files, because they are not the same kind of document:

    docs/           this project's knowledge — every check applies
    the repo root   CLAUDE.md, README.md — every check but the index
    ~/Claude/       Pierre's cross-project files — links and home paths only

`~/Claude/` gets the narrow treatment deliberately. Those files are loaded in
EVERY project, so a bare `docs/todo.md` in one of them means "the current
project's", not this repo's, and checking it here would be asserting something
the file never claimed. For the same reason their code names are not checked
against this repo's source.
"""

import os
import re
import sys

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DOCS_ROOT = os.path.join(REPO_ROOT, "docs")
CLAUDE_ROOT = os.path.expanduser("~/Claude")

# Where a name the docs mention could legitimately live.
SOURCE_GLOBS = ["local", "media/data/scripts", ".github/workflows"]

SOURCE_EXTENSIONS = (".js", ".py", ".jst", ".cst", ".yml", ".yaml")

# A backticked token is only worth checking as a code name if it is shaped like
# one. Prose words in backticks are the common case and must not be flagged.
NAME_SHAPE = re.compile(r"^(GL\.)?[A-Za-z_][A-Za-z0-9_]*(\(\))?$")

# Words that pass NAME_SHAPE but are English, JSON or WP vocabulary, not names
# this repo defines.
NAME_STOPLIST = {
	"published", "comments", "keywords", "badges", "access", "types", "notes", "actual",
	"pavement", "unpaved", "potholes", "rugged", "dirt", "walk", "hike", "boat", "lake",
	"park", "tent", "picnic", "home", "campground", "homepage", "reservation", "grid",
	"table", "view", "search", "booklet", "dataset", "counts", "options", "known", "file",
	"label", "title", "name", "date", "image", "links", "location", "legs", "haversine",
	"driving", "main", "open", "closed", "publish", "draft", "null", "true", "false",
	"width", "align", "field", "params", "url", "img", "slug", "base", "type", "text",
}

# A line carrying one of these is describing something that was taken out, so
# the symbol on it is not being claimed to exist.
# How close a filename has to sit to a symbol to count as claiming it.
NAME_BINDING_WINDOW = 40

RETIREMENT_WORDS = (
	"retired", "removed", "deleted", "obsolete", "dead", "gone", "dropped", "died",
	"no longer", "was ", "old ", "used to", "replaced", "renamed from", "not moved",
	"does not exist", "no page-map", "never existed",
)

# A count of what the data holds right now does not belong in a doc — it is a
# cache of something measurable, with nothing to invalidate it. See
# docs/README.md, "These files are not a cache of the repo". Dated migration
# records are history and stay true, so a line naming a year is skipped.
CACHE_PATTERNS = (
	re.compile(r"\b\d+ of (?:the )?\d+\b"),
	re.compile(r"\ball \d+ (?:pages|rows|files|JSONs|destinations|entries|records|templates)\b"),
)
DATED_LINE = re.compile(r"20\d\d-\d\d-\d\d")

LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
BACKTICK_PATTERN = re.compile(r"`([^`]+)`")
REPO_PREFIXES = ("media/", "pages/", "local/", "docs/", "logs/", "posts/", ".claude/", ".github/")


# Every markdown file under a root, sorted so a run is reproducible.
def findDocFiles(docsRoot):
	docPaths = []
	for dirPath, dirNames, fileNames in os.walk(docsRoot):
		dirNames.sort()
		for fileName in sorted(fileNames):
			if fileName.endswith(".md"):
				docPaths.append(os.path.join(dirPath, fileName))
	return docPaths


# The markdown sitting directly in the repo root — CLAUDE.md and README.md. Not
# a walk: everything deeper belongs to one of the other roots.
def findRootFiles(repoRoot):
	rootPaths = []
	for fileName in sorted(os.listdir(repoRoot)):
		if fileName.endswith(".md"):
			rootPaths.append(os.path.join(repoRoot, fileName))
	return rootPaths


def readText(path):
	with open(path, encoding="utf-8") as handle:
		text = handle.read()
	return text


# Repo-relative, so a finding can be pasted straight into a message. A file
# outside the repo keeps its ~-abbreviated absolute path — "../../Claude/x.md"
# would be unreadable and unpasteable.
def relative(path):
	if path.startswith(REPO_ROOT + os.sep):
		relPath = os.path.relpath(path, REPO_ROOT)
		return relPath
	home = os.path.expanduser("~")
	relPath = path.replace(home, "~", 1) if path.startswith(home) else path
	return relPath


# A placeholder stands for a name the reader supplies, or an elision standing in
# for the rest of a path; there is nothing on disk to check either against.
def isPlaceholder(token):
	placeholder = any(character in token for character in "<>{}*…") or "..." in token
	return placeholder


# CHECK: every relative markdown link resolves to a file that exists.
def checkLinks(docPaths):
	findings = []
	for docPath in docPaths:
		for match in LINK_PATTERN.finditer(readText(docPath)):
			target = match.group(2).split("#")[0].strip()
			if not target or target.startswith(("http://", "https://", "mailto:")):
				continue
			resolved = os.path.normpath(os.path.join(os.path.dirname(docPath), target))
			if not os.path.exists(resolved):
				findings.append(f"{relative(docPath)}: [{match.group(1)}]({target}) does not resolve")
	return findings


# Every backticked token, with the file and the line it came from. The line
# travels with the token because a sentence saying a thing is GONE is not
# claiming it is there — same rule the names check uses.
def collectBacktickedTokens(docPaths):
	tokens = []
	for docPath in docPaths:
		for line in readText(docPath).splitlines():
			for match in BACKTICK_PATTERN.finditer(line):
				tokens.append({"token": match.group(1).strip(), "doc": docPath, "line": line})
	return tokens


def saysItIsGone(line):
	lowered = line.lower()
	gone = any(word in lowered for word in RETIREMENT_WORDS)
	return gone


# Where a backticked path is rooted, or nothing when it is not a path at all.
# A repo path is only meaningful for files that belong to this project — see the
# module docstring on why ~/Claude/ is excluded from that half.
def resolvePathToken(token, allowRepoPaths):
	if " " in token or isPlaceholder(token):
		return None
	target = token.rstrip("/")
	if target.startswith("~/"):
		resolved = os.path.expanduser(target)
		return resolved
	if allowRepoPaths and target.startswith(REPO_PREFIXES):
		resolved = os.path.join(REPO_ROOT, target)
		return resolved
	return None


# CHECK: every backticked repo or home path exists on disk.
def checkPaths(tokens, allowRepoPaths=True):
	findings = []
	seen = set()
	for entry in tokens:
		if saysItIsGone(entry["line"]):
			continue
		resolved = resolvePathToken(entry["token"], allowRepoPaths)
		if resolved is None:
			continue
		key = (resolved, entry["doc"])
		if key in seen:
			continue
		seen.add(key)
		if not os.path.exists(resolved):
			findings.append(f"{relative(entry['doc'])}: `{entry['token']}` does not exist")
	return findings


# Every source file this repo owns, by basename, with its text.
def collectSourceFiles():
	byName = {}
	for globRoot in SOURCE_GLOBS:
		for dirPath, dirNames, fileNames in os.walk(os.path.join(REPO_ROOT, globRoot)):
			for fileName in sorted(fileNames):
				if fileName.endswith(SOURCE_EXTENSIONS):
					byName.setdefault(fileName, readText(os.path.join(dirPath, fileName)))
	return byName


# CHECK: a symbol a doc ATTRIBUTES to one of our source files still exists in
# that file.
#
# Scoped to the line, and to the named file, on purpose. A doc naming a symbol
# on its own says nothing about where it should live — WP fields, FileBird
# params and external dataset columns all read as code and none of them are
# ours. "sync.js `generateGalleryJsons`" is a claim about this repo, and that is
# the claim worth testing.
#
# A line that says the symbol is GONE is not a claim that it exists, so the
# retirement words skip it — documenting what was removed is the docs doing
# their job.
def checkNames(docPaths, sourceFiles):
	findings = []
	for docPath in docPaths:
		for line in readText(docPath).splitlines():
			lowered = line.lower()
			if any(word in lowered for word in RETIREMENT_WORDS):
				continue
			for match in BACKTICK_PATTERN.finditer(line):
				bare = symbolOf(match.group(1).strip())
				if not bare:
					continue
				named = filesNear(line, match.start(), match.end(), sourceFiles)
				if not named:
					continue
				# Absent from EVERY source file, not just the one named. A symbol
				# that merely moved between our files is a misattribution, not
				# rot, and reporting those buries the ones that are gone.
				if not any(bare in text for text in sourceFiles.values()):
					findings.append(f"{relative(docPath)}: `{match.group(1)}` is attributed to {', '.join(named)} but exists in no source file")
	return findings


# The bare symbol a backticked token stands for, or nothing when the token is
# prose, a placeholder, or a word too common to be a name.
def symbolOf(token):
	if isPlaceholder(token) or not NAME_SHAPE.match(token):
		return None
	bare = token.rstrip("()")
	if bare.startswith("GL."):
		bare = bare[3:]
	if len(bare) < 5 or bare.lower() in NAME_STOPLIST:
		return None
	if not (any(character.isupper() for character in bare[1:]) or "_" in bare):
		return None
	return bare


# The source files named close enough to a symbol to be claiming it — "X in
# gettinglost.jst", "sync.js `X`", "gettinglost.jst's `X`". A filename further
# down the same sentence is talking about something else, and binding to it is
# what turned this check into noise on the first draft.
def filesNear(line, start, end, sourceFiles):
	window = line[max(0, start - NAME_BINDING_WINDOW):end + NAME_BINDING_WINDOW]
	named = [fileName for fileName in sourceFiles if fileName in window]
	return named


# CHECK: docs/README.md lists every doc, and projects/README.md every project.
# The two indexes split the job — project files are indexed by the projects
# README, which is the only place a project's status lives.
def checkIndex(docPaths):
	findings = []
	docsIndex = readText(os.path.join(DOCS_ROOT, "README.md"))
	projectsIndex = readText(os.path.join(DOCS_ROOT, "projects", "README.md"))
	for docPath in docPaths:
		relPath = relative(docPath)
		fileName = os.path.basename(docPath)
		if relPath in ("docs/README.md", "docs/projects/README.md"):
			continue
		index, indexName = (projectsIndex, "docs/projects/README.md") if "/projects/" in relPath else (docsIndex, "docs/README.md")
		if fileName not in index:
			findings.append(f"{indexName} does not list {relPath}")
	return findings


# CHECK: no doc states a count of what the data holds right now. Such a count is
# true for a day and cannot announce that it went stale; say the relationship and
# query the JSON for the number. A line carrying a date is a migration record —
# history, which stays true — and is skipped.
def checkCache(docPaths):
	findings = []
	for path in docPaths:
		for number, line in enumerate(readText(path).splitlines(), start=1):
			if DATED_LINE.search(line):
				continue
			for pattern in CACHE_PATTERNS:
				match = pattern.search(line)
				if match and line[max(0, match.start() - 1)] == '"':
					continue  # quoted — the rule quoting an example of itself
				if match:
					findings.append(f"{relative(path)}:{number}: counts live data — \"{match.group(0)}\"")
					break
	return findings


# CHECK: the house format claim in docs/conventions/json-format.md — that a
# jsonio round-trip is byte-identical, which is what makes "route even
# single-field edits through python" safe. A file that fails this would come
# back reformatted from any edit.
def checkFormat():
	findings = []
	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
	try:
		import jsonio
	except ImportError:
		return ["local/tools/jsonio.py could not be imported"]
	for dirPath, dirNames, fileNames in os.walk(os.path.join(REPO_ROOT, "media", "data")):
		dirNames.sort()
		for fileName in sorted(fileNames):
			if not fileName.endswith(".json"):
				continue
			full = os.path.join(dirPath, fileName)
			if jsonio.dumps(jsonio.load(full)).rstrip("\n") + "\n" != readText(full):
				findings.append(f"{relative(full)} is not in the jsonio house format")
	return findings


# The report: one section per check, numbered as plain text so the numbers
# survive being pasted into a reply.
def printReport(sections):
	total = 0
	for name, findings in sections:
		print(f"{name} — {len(findings)}")
		for number, finding in enumerate(findings, start=1):
			print(f"  {number}. {finding}")
		total += len(findings)
		print()
	print(f"{total} findings")
	return total


def main(argv):
	verbose = "--verbose" in argv
	docPaths = findDocFiles(DOCS_ROOT)
	rootPaths = findRootFiles(REPO_ROOT)
	claudePaths = findDocFiles(CLAUDE_ROOT) if os.path.isdir(CLAUDE_ROOT) else []

	# docs/ and the repo root are this project's own files and are checked the
	# same way; ~/Claude/ is checked narrowly (docstring).
	projectPaths = docPaths + rootPaths
	sourceFiles = collectSourceFiles()
	projectTokens = collectBacktickedTokens(projectPaths)
	claudeTokens = collectBacktickedTokens(claudePaths)

	if verbose:
		print(f"{len(docPaths)} docs, {len(rootPaths)} root, {len(claudePaths)} in ~/Claude, "
			f"{len(projectTokens) + len(claudeTokens)} backticked tokens, {len(sourceFiles)} source files\n")

	sections = [
		("links", checkLinks(projectPaths + claudePaths)),
		("paths", checkPaths(projectTokens) + checkPaths(claudeTokens, allowRepoPaths=False)),
		("index", checkIndex(docPaths)),
		("names", checkNames(projectPaths, sourceFiles)),
		("cache", checkCache(projectPaths)),
		("format", checkFormat()),
	]
	total = printReport(sections)
	return 1 if total else 0


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
