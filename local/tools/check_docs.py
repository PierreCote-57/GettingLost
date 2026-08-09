#!/usr/bin/env python3
"""Documentation validation pass — the mechanical half.

Checks what a script can check about `docs/`: that every pointer resolves and
every name it uses still exists. It REPORTS; it never edits, and it never drops
a finding for being uninteresting.

Prose is out of scope on purpose. Whether a paragraph still describes how the
site works is a reading job, and no script can do it. What lives here is the
part that rots silently: a link to a renamed file, a path that moved, a folder
tree that drifted from disk, a function the code no longer has.

    check_docs.py                 the report
    check_docs.py --verbose       also list what each check looked at

Five checks:

    links     every relative markdown link resolves
    paths     every backticked repo path exists
    index     docs/README.md lists every doc; projects/README.md every project
    tree      the folders.md hierarchy matches media/data and pages on disk
    names     every code symbol and filename the docs name still exists

A folder line in the folders.md tree annotated "WP only" is skipped by the tree
check — it describes a folder that lives in WordPress with no repo counterpart.
"""

import os
import re
import sys

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DOCS_ROOT = os.path.join(REPO_ROOT, "docs")

# Where a name the docs mention could legitimately live.
SOURCE_GLOBS = ["local", "media/data/scripts", ".github/workflows"]

SOURCE_EXTENSIONS = (".js", ".py", ".jst", ".cst", ".yml", ".yaml")

# Folders under media/data that the tree in folders.md deliberately does not
# mirror; the file says so in its own words right under the tree.
TREE_EXEMPT_ROOTS = ("scripts", "posts")

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
)

LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
BACKTICK_PATTERN = re.compile(r"`([^`]+)`")
FOLDER_LINE_PATTERN = re.compile(r"^(\s*)([A-Za-z0-9._-]+)/\s*(←.*)?$")
REPO_PREFIXES = ("media/", "pages/", "local/", "docs/", "logs/", "posts/", ".claude/", ".github/")


# Every markdown file under docs/, sorted so a run is reproducible.
def findDocFiles(docsRoot):
	docPaths = []
	for dirPath, dirNames, fileNames in os.walk(docsRoot):
		dirNames.sort()
		for fileName in sorted(fileNames):
			if fileName.endswith(".md"):
				docPaths.append(os.path.join(dirPath, fileName))
	return docPaths


def readText(path):
	with open(path, encoding="utf-8") as handle:
		text = handle.read()
	return text


# Repo-relative, so a finding can be pasted straight into a message.
def relative(path):
	relPath = os.path.relpath(path, REPO_ROOT)
	return relPath


# A placeholder stands for a name the reader supplies; there is nothing on disk
# to check it against.
def isPlaceholder(token):
	placeholder = any(character in token for character in "<>{}*")
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


# Every backticked token in the docs, with the file it came from.
def collectBacktickedTokens(docPaths):
	tokens = []
	for docPath in docPaths:
		for match in BACKTICK_PATTERN.finditer(readText(docPath)):
			tokens.append({"token": match.group(1).strip(), "doc": docPath})
	return tokens


# CHECK: every backticked path that looks like a repo path exists on disk.
def checkPaths(tokens):
	findings = []
	seen = set()
	for entry in tokens:
		token = entry["token"]
		if " " in token or isPlaceholder(token) or not token.startswith(REPO_PREFIXES):
			continue
		target = token.rstrip("/")
		key = (target, entry["doc"])
		if key in seen:
			continue
		seen.add(key)
		if not os.path.exists(os.path.join(REPO_ROOT, target)):
			findings.append(f"{relative(entry['doc'])}: `{token}` does not exist")
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


# The folder hierarchy written in folders.md, as a set of paths. It is the
# fenced block holding the most folder lines; the file's other blocks list the
# four locations and hold no hierarchy.
def parseFolderTree(text):
	blocks = text.split("```")
	best = []
	for block in blocks:
		paths = []
		stack = []
		for line in block.splitlines():
			match = FOLDER_LINE_PATTERN.match(line)
			if not match:
				continue
			annotation = match.group(3) or ""
			depth = len(match.group(1)) // 2
			stack = stack[:depth] + [match.group(2)]
			if "WP only" in annotation:
				continue
			paths.append("/".join(stack))
		if len(paths) > len(best):
			best = paths
	tree = set(best)
	return tree


# Every folder on disk the tree is meant to mirror.
def collectDiskFolders(root, exemptRoots):
	folders = set()
	for dirPath, dirNames, fileNames in os.walk(os.path.join(REPO_ROOT, root)):
		relPath = os.path.relpath(dirPath, os.path.join(REPO_ROOT, root))
		if relPath == ".":
			continue
		if relPath.split(os.sep)[0] in exemptRoots:
			continue
		folders.add(relPath.replace(os.sep, "/"))
	return folders


# CHECK: the folders.md tree matches media/data, and holds every pages/ folder.
# media/data is the strict comparison — it carries a folder per page, so the
# tree and the disk should agree in both directions. pages/ holds no leaf page
# folders, so only its extras are a finding.
def checkTree():
	findings = []
	treePath = os.path.join(DOCS_ROOT, "conventions", "folders.md")
	tree = parseFolderTree(readText(treePath))
	dataFolders = collectDiskFolders("media/data", TREE_EXEMPT_ROOTS)
	pageFolders = collectDiskFolders("pages", ())
	for missing in sorted(tree - dataFolders - pageFolders):
		findings.append(f"docs/conventions/folders.md: `{missing}/` is in the tree but not on disk")
	for extra in sorted(dataFolders - tree):
		findings.append(f"docs/conventions/folders.md: `media/data/{extra}/` is on disk but not in the tree")
	for extra in sorted(pageFolders - tree):
		findings.append(f"docs/conventions/folders.md: `pages/{extra}/` is on disk but not in the tree")
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
	tokens = collectBacktickedTokens(docPaths)
	sourceFiles = collectSourceFiles()

	if verbose:
		print(f"{len(docPaths)} docs, {len(tokens)} backticked tokens, {len(sourceFiles)} source files\n")

	sections = [
		("links", checkLinks(docPaths)),
		("paths", checkPaths(tokens)),
		("index", checkIndex(docPaths)),
		("tree", checkTree()),
		("names", checkNames(docPaths, sourceFiles)),
	]
	total = printReport(sections)
	return 1 if total else 0


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
