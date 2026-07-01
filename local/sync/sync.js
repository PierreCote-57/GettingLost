#!/usr/bin/env node
/**
 * sync.js
 *
 * Pushes this repo's content to WordPress, overwriting whatever is
 * currently live — no diffing, no confirmation prompt. This is the
 * "GitHub is master" sync: run it, and WordPress is made to match
 * the repo, full stop.
 *
 * Two kinds of targets:
 *
 *   1. PAGES — full-content overwrite via the WP REST API
 *      (PUT/POST /wp/v2/pages/<id> with the repo's HTML as `content`).
 *      Uses local/config/page-map.json to know which WordPress page ID
 *      corresponds to each repo file.
 *
 *   2. FILES (JSON data files + .jst scripts) — uploaded to the media
 *      library at /wp-content/uploads/<filename>. WordPress does NOT
 *      overwrite a same-named file by default (it silently appends
 *      "-1", "-2", etc. instead), so to get a true overwrite at the
 *      same URL this script:
 *        a. looks up the existing media item by filename
 *        b. deletes it (force=true, permanent — no trash)
 *        c. re-uploads a new media item with the same filename
 *      This briefly 404s the file while the delete/recreate happens
 *      (typically well under a second), which is an accepted tradeoff
 *      for keeping the same data file architecture every page already
 *      depends on.
 *
 * Auth: WordPress Application Password (Basic Auth), provided via
 * the WP_USER and WP_APP_PASSWORD environment variables (GitHub
 * Secrets in the Action). Site URL via WP_SITE_URL.
 *
 * Blog posts are intentionally untouched — this script only ever
 * looks at /wp/v2/pages and /wp/v2/media, never /wp/v2/posts.
 */

const fs = require("fs");
const path = require("path");

// ---------------------------------------------------------------------
// Top-level constants (ALL CAPS) — grouped here for easy reference
// and adjustment. Everything else in the file is functions and logic;
// if you need to change a path, env var name, or mode flag, it's here.
// ---------------------------------------------------------------------

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const PAGES_ROOT = path.join(REPO_ROOT, "pages");
const MEDIA_ROOT = path.join(REPO_ROOT, "media");

const INCREMENTAL =
  process.argv.some((a) => a.startsWith("--changed-files=")) ||
  process.argv.some((a) => a.startsWith("--removed-files="));

const WP_SITE_URL = requireEnv("WP_SITE_URL").replace(/\/$/, "");
const WP_USER = requireEnv("WP_USER");
const WP_APP_PASSWORD = requireEnv("WP_APP_PASSWORD");

const AUTH_HEADER =
  "Basic " + Buffer.from(`${WP_USER}:${WP_APP_PASSWORD}`).toString("base64");

// Intentionally NOT read via requireEnv(): FileBird folder filing is a
// best-effort, log-only feature (see syncOneFileToFileBird below). A
// missing or bad token should degrade that one feature, never crash
// the actual WordPress content sync.
const FILEBIRD_TOKEN = process.env.FILEBIRD_TOKEN || null;

// ---------------------------------------------------------------------
// Incremental mode
//
// Invoked with --changed-files=<path> and --removed-files=<path>,
// each pointing to a plain text file (one repo-relative path per
// line), built by the push workflow from the GitHub push event's
// commits[].added / .modified / .removed lists.
//
//   - With no flags: full-overwrite mode, identical to the original
//     script (used by the manual workflow_dispatch trigger).
//   - With flags: only files in --changed-files are synced. Files in
//     --removed-files are logged as a warning and otherwise ignored —
//     this script never deletes content from WordPress automatically.
// ---------------------------------------------------------------------

function readLines(flagName) {
  const arg = process.argv.find((a) => a.startsWith(`${flagName}=`));
  if (!arg) return null;

  const listPath = path.resolve(arg.slice(flagName.length + 1));
  if (!fs.existsSync(listPath)) {
    console.warn(`${flagName} path not found (${listPath}) — treating as empty.`);
    return [];
  }
  return fs
    .readFileSync(listPath, "utf8")
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
}

let CHANGED = null;
if (INCREMENTAL) {
  const changedList = readLines("--changed-files") || [];
  const removedList = readLines("--removed-files") || [];

  if (removedList.length > 0) {
    console.warn(
      `[incremental] ${removedList.length} file(s) removed in this push — skipping, NOT deleting from WordPress:\n` +
        removedList.map((f) => `  - ${f}`).join("\n")
    );
  }

  const localChanged = changedList.some((f) => f.startsWith("local/"));

  if (localChanged) {
    // Something under local/ changed — could be page-map.json (mappings
    // may have shifted) or the sync script itself (its own filtering
    // logic might be the thing that's buggy, so don't trust it). Safest
    // move: drop back to full-overwrite mode, identical to a manual
    // workflow_dispatch run.
    console.log(
      "[incremental] A file under local/ changed (config and/or sync script) — falling back to a full sync instead of incremental, to be safe."
    );
    CHANGED = null;
  } else {
    CHANGED = { files: new Set(changedList) };
    console.log(`[incremental] Running in incremental mode — ${CHANGED.files.size} changed file(s).`);
  }
} else {
  console.log("Running in full-overwrite mode (no --changed-files/--removed-files supplied).");
}

function requireEnv(name) {
  const value = process.env[name];
  if (!value) {
    console.error(`Missing required environment variable: ${name}`);
    process.exit(1);
  }
  return value;
}

function wpFetch(endpoint, options = {}) {
  const url = `${WP_SITE_URL}/wp-json/wp/v2${endpoint}`;
  return fetch(url, {
    ...options,
    headers: {
      Authorization: AUTH_HEADER,
      ...(options.headers || {}),
    },
  });
}

function fbFetch(endpoint, options = {}) {
  const url = `${WP_SITE_URL}/wp-json/filebird/public/v1${endpoint}`;
  return fetch(url, {
    ...options,
    headers: {
      Authorization: `Bearer ${FILEBIRD_TOKEN}`,
      ...(options.headers || {}),
    },
  });
}

// ---------------------------------------------------------------------
// PAGES sync
// ---------------------------------------------------------------------

function buildPageFileMap() {
  // slug -> { filePath, relPath } — built from one recursive walk of
  // pages/, so the actual folder a page lives in (lakes/parks/
  // campgrounds/templates/special/...) never has to be hardcoded or
  // kept in sync with page-map.json's category names.
  const map = new Map();
  if (!fs.existsSync(PAGES_ROOT)) return map;

  const entries = fs.readdirSync(PAGES_ROOT, { recursive: true });
  for (const entry of entries) {
    if (!entry.endsWith(".html")) continue;
    const slug = path.basename(entry, ".html");
    const filePath = path.join(PAGES_ROOT, entry);
    const relPath = path.posix.join("pages", entry.split(path.sep).join("/"));
    map.set(slug, { filePath, relPath });
  }
  return map;
}

function checkForUnmappedPages(pageMap, pageFileMap) {
  const mappedSlugs = new Set();
  for (const slugToId of Object.values(pageMap)) {
    for (const slug of Object.keys(slugToId)) mappedSlugs.add(slug);
  }

  const unmapped = [];
  for (const [slug, entry] of pageFileMap) {
    if (!mappedSlugs.has(slug)) {
      unmapped.push(entry.relPath);
    }
  }

  if (unmapped.length > 0) {
    console.warn(
      `[pages] ${unmapped.length} page file(s) found with no entry in local/config/page-map.json — NOT synced:\n` +
        unmapped.map((f) => `  - ${f}`).join("\n") +
        `\n  Create the page in WordPress, add its slug → page ID to local/config/page-map.json, then push again.`
    );
  }
}

async function syncPages(pageFolderCache) {
  const pageMapPath = path.join(REPO_ROOT, "local", "config", "page-map.json");
  const pageMap = JSON.parse(fs.readFileSync(pageMapPath, "utf8"));

  const pageFileMap = buildPageFileMap();
  checkForUnmappedPages(pageMap, pageFileMap);

  let successCount = 0;
  let failCount = 0;

  for (const [category, slugToId] of Object.entries(pageMap)) {
    for (const [slug, pageId] of Object.entries(slugToId)) {
      const entry = pageFileMap.get(slug);

      if (!entry) {
        console.warn(`[pages] ${category}/${slug}: no file found anywhere under pages/ — skipping.`);
        continue;
      }

      if (CHANGED && !CHANGED.files.has(entry.relPath)) {
        continue; // not part of this push — leave it alone
      }

      const content = fs.readFileSync(entry.filePath, "utf8");

      try {
        const res = await wpFetch(`/pages/${pageId}`, {
          method: "POST", // WP REST API uses POST for partial/full updates
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content }),
        });

        if (!res.ok) {
          const body = await res.text();
          console.error(`[pages] FAILED ${category}/${slug} (id ${pageId}): HTTP ${res.status} — ${body}`);
          failCount++;
          continue;
        }

        const data = await res.json();
        if (data._content_warnings) {
          console.warn(`[pages] ${category}/${slug} (id ${pageId}): saved with warnings:`, data._content_warnings);
        } else {
          console.log(`[pages] OK ${category}/${slug} (id ${pageId})`);
        }
        await syncOnePageToFileBird(pageFolderCache, pageId, entry.relPath);
        successCount++;
      } catch (err) {
        console.error(`[pages] ERROR ${category}/${slug} (id ${pageId}):`, err.message);
        failCount++;
      }
    }
  }

  return { successCount, failCount };
}

// ---------------------------------------------------------------------
// FILES sync (JSON data files + .jst scripts) — delete-then-recreate
// ---------------------------------------------------------------------

function guessMimeFromExt(filename) {
  if (filename.endsWith(".jst")) return "text/text";
  if (filename.endsWith(".json")) return "application/json";
  return "application/octet-stream";
}

async function findExistingMediaIdByFilename(filename) {
  // WordPress media "search" matches title, not filename directly, but
  // titles here are always set to the filename minus extension, and
  // the source_url ends in the exact filename — search narrows the
  // candidate list, then we confirm by checking source_url.
  const titleGuess = filename.replace(/\.(json|jst)$/, "");
  const res = await wpFetch(`/media?search=${encodeURIComponent(titleGuess)}&per_page=20`);
  if (!res.ok) {
    throw new Error(`media search failed: HTTP ${res.status}`);
  }
  const items = await res.json();
  const match = items.find((item) => item.source_url && item.source_url.endsWith(`/${filename}`));
  return match ? match.id : null;
}

async function deleteMedia(id) {
  const res = await wpFetch(`/media/${id}?force=true`, { method: "DELETE" });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`delete failed: HTTP ${res.status} — ${body}`);
  }
}

async function uploadMedia(filename, fileBuffer, mimeType) {
  const res = await wpFetch(`/media`, {
    method: "POST",
    headers: {
      "Content-Type": mimeType,
      "Content-Disposition": `attachment; filename="${filename}"`,
    },
    body: fileBuffer,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`upload failed: HTTP ${res.status} — ${body}`);
  }
  return res.json();
}

async function syncOneFileToWordPress(relSubPath, filename, fileBuffer, mimeType) {
  try {
    const existingId = await findExistingMediaIdByFilename(filename);
    if (existingId) {
      await deleteMedia(existingId);
    }
    const uploaded = await uploadMedia(filename, fileBuffer, mimeType);
    console.log(`[files] OK ${relSubPath}${existingId ? " (overwritten)" : " (new)"}`);
    return uploaded.id;
  } catch (err) {
    console.error(`[files] FAILED ${relSubPath}:`, err.message);
    return null;
  }
}

// ---------------------------------------------------------------------
// FILEBIRD folder filing — best effort, log-only. A FileBird problem
// (no token, network error, bad folder data, etc.) never affects
// syncFiles()'s successCount/failCount; it's only ever logged.
//
// A file's path relative to media/ (e.g. "data/lakes/amor-lake.json")
// is mirrored EXACTLY into FileBird as nested folders, case-sensitive
// — "data" then "lakes" — with the file assigned to the innermost one.
// Folders are created on demand the first time they're needed.
// ---------------------------------------------------------------------

async function loadFileBirdFolderTree() {
  const cache = new Map(); // lowercase full path (e.g. "data/lakes") -> folder id
  const res = await fbFetch("/folders");
  if (!res.ok) {
    throw new Error(`folder list failed: HTTP ${res.status}`);
  }
  const json = await res.json();
  const roots = (json.data && json.data.folders) || [];

  function walk(nodes, parentPath) {
    for (const node of nodes) {
      const fullPath = parentPath ? `${parentPath}/${node.text}` : node.text;
      cache.set(fullPath.toLowerCase(), node.id);
      if (node.children && node.children.length) {
        walk(node.children, fullPath);
      }
    }
  }
  walk(roots, "");
  return cache;
}

async function ensureFileBirdFolderPath(folderCache, segments) {
  let parentId = 0;
  let pathSoFar = "";

  for (const name of segments) {
    pathSoFar = pathSoFar ? `${pathSoFar}/${name}` : name;
    const cacheKey = pathSoFar.toLowerCase();

    if (!folderCache.has(cacheKey)) {
      const res = await fbFetch("/folders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, parent_id: parentId }),
      });
      if (!res.ok) {
        const body = await res.text();
        throw new Error(`create folder "${pathSoFar}" failed: HTTP ${res.status} — ${body}`);
      }
      const created = await res.json();
      const newId = created.data && created.data.id;
      if (!newId) {
        throw new Error(`create folder "${pathSoFar}" returned no id: ${JSON.stringify(created)}`);
      }
      folderCache.set(cacheKey, newId);
      console.log(`[filebird] created folder "${pathSoFar}" (id ${newId})`);
    }

    parentId = folderCache.get(cacheKey);
  }

  return parentId; // id of the deepest (innermost) folder in the path
}

async function syncOneFileToFileBird(folderCache, mediaId, relSubPath) {
  if (!folderCache) return; // disabled this run — no token, or initial load failed

  const segments = path.posix.dirname(relSubPath).split("/").filter(Boolean);
  if (segments.length === 0) return; // file sits directly in media/ root, nothing to file into

  try {
    const folderId = await ensureFileBirdFolderPath(folderCache, segments);
    const res = await fbFetch("/folder/set-attachment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ folder: folderId, ids: [mediaId] }),
    });
    const json = await res.json().catch(() => null);
    if (!res.ok || !json || json.success !== true) {
      throw new Error(`set-attachment failed: HTTP ${res.status} — ${JSON.stringify(json)}`);
    }
    console.log(`[filebird] filed ${relSubPath} -> ${segments.join("/")}`);
  } catch (err) {
    console.warn(`[filebird] FAILED to file ${relSubPath}:`, err.message);
  }
}

// ---------------------------------------------------------------------
// FILEBIRD PAGE FOLDER filing — best effort, log-only. Same token and
// degradation strategy as media folder filing above.
//
// A page's path relative to pages/ (e.g. "van/howto/howto-awning.html")
// is mirrored into FileBird page folders: the dirname segments become
// nested folders ("Van" → "HowTo") and the page is assigned to the
// innermost one. Folder lookup is case-insensitive so existing
// Title-Case folders ("HowTo") are matched by lowercase repo segments.
// ---------------------------------------------------------------------

async function loadFileBirdPageFolderTree() {
  const cache = new Map(); // lowercase full path -> folder id
  const res = await fbFetch("/post-type-folders/?post_type=page");
  if (!res.ok) {
    throw new Error(`page folder list failed: HTTP ${res.status}`);
  }
  const json = await res.json();
  const roots = Array.isArray(json.data?.folders)
    ? json.data.folders
    : Array.isArray(json.data)
    ? json.data
    : [];

  function walk(nodes, parentPath) {
    for (const node of nodes) {
      const name = node.text || node.title || "";
      if (!name) continue;
      const fullPath = parentPath ? `${parentPath}/${name}` : name;
      cache.set(fullPath.toLowerCase(), node.id);
      if (node.children && node.children.length) walk(node.children, fullPath);
    }
  }
  walk(roots, "");
  return cache;
}

async function ensureFileBirdPageFolderPath(pageFolderCache, segments) {
  let parentId = 0;
  let pathSoFar = "";

  for (const name of segments) {
    const pathKey = pathSoFar ? `${pathSoFar}/${name}` : name;
    const cacheKey = pathKey.toLowerCase();

    if (!pageFolderCache.has(cacheKey)) {
      const displayName = name.charAt(0).toUpperCase() + name.slice(1);
      const res = await fbFetch("/post-type-folders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ post_type: "page", title: displayName, parent: parentId }),
      });

      if (!res.ok) {
        const body = await res.text();
        let parsed = null;
        try { parsed = JSON.parse(body); } catch (_) {}
        if (parsed?.code === "folder_name_exist") {
          // Folder exists but wasn't in our cache — reload tree to recover the id
          const fresh = await loadFileBirdPageFolderTree();
          for (const [k, v] of fresh) pageFolderCache.set(k, v);
          if (!pageFolderCache.has(cacheKey)) {
            throw new Error(`create page folder "${pathKey}" failed and folder not found after reload`);
          }
          console.log(`[filebird:pages] recovered existing folder "${pathKey}" after cache miss`);
        } else {
          throw new Error(`create page folder "${pathKey}" failed: HTTP ${res.status} — ${body}`);
        }
      } else {
        const created = await res.json();
        // API returns either [{id, ...}] or {data: {id: ...}}
        const newId = Array.isArray(created) ? created[0]?.id : (created.data && created.data.id);
        if (!newId) {
          throw new Error(`create page folder "${pathKey}" returned no id: ${JSON.stringify(created)}`);
        }
        pageFolderCache.set(cacheKey, newId);
        console.log(`[filebird:pages] created folder "${pathKey}" (id ${newId})`);
      }
    }

    parentId = pageFolderCache.get(cacheKey);
    pathSoFar = pathKey;
  }

  return parentId;
}

async function syncOnePageToFileBird(pageFolderCache, pageId, relPath) {
  if (!pageFolderCache) return;

  // relPath is like "pages/van/howto/howto-temperature-control.html"
  const afterPages = relPath.startsWith("pages/") ? relPath.slice("pages/".length) : relPath;
  const segments = path.posix.dirname(afterPages).split("/").filter((s) => s && s !== ".");
  if (segments.length === 0) return; // file sits directly in pages/ root

  try {
    const folderId = await ensureFileBirdPageFolderPath(pageFolderCache, segments);
    const res = await fbFetch("/post-type-folder/set-posts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ post_type: "page", folderId, ids: [pageId] }),
    });
    const json = await res.json().catch(() => null);
    if (!res.ok || !json) {
      throw new Error(`set-posts failed: HTTP ${res.status} — ${JSON.stringify(json)}`);
    }
    console.log(`[filebird:pages] filed ${relPath} -> ${segments.join("/")}`);
  } catch (err) {
    console.warn(`[filebird:pages] FAILED to file ${relPath}:`, err.message);
  }
}

async function syncFiles(fileBirdFolderCache) {
  let successCount = 0;
  let failCount = 0;

  if (!fs.existsSync(MEDIA_ROOT)) {
    console.warn(`[files] media root not found at ${MEDIA_ROOT} — nothing to sync.`);
    return { successCount, failCount };
  }

  const allEntries = fs.readdirSync(MEDIA_ROOT, { recursive: true });
  const filenames = allEntries.filter((f) => f.endsWith(".json") || f.endsWith(".jst"));

  for (const relSubPath of filenames) {
    const filePath = path.join(MEDIA_ROOT, relSubPath);
    const filename = path.basename(filePath);
    const relPath = path.posix.relative(REPO_ROOT, filePath);

    if (CHANGED && !CHANGED.files.has(relPath)) {
      continue; // not part of this push — leave it alone
    }

    const fileBuffer = fs.readFileSync(filePath);
    const mimeType = guessMimeFromExt(filename);

    const mediaId = await syncOneFileToWordPress(relSubPath, filename, fileBuffer, mimeType);

    if (mediaId) {
      successCount++;
      await syncOneFileToFileBird(fileBirdFolderCache, mediaId, relSubPath);
    } else {
      failCount++;
    }
  }

  return { successCount, failCount };
}

// ---------------------------------------------------------------------
// Gallery JSON (media/special/gallery-data/) is picked up automatically
// by syncFiles()'s recursive walk of media/ — no special-casing needed.
// ---------------------------------------------------------------------

// ---------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------

async function main() {
  console.log(`Syncing to ${WP_SITE_URL} ...\n`);

  let fileBirdFolderCache = null;
  if (FILEBIRD_TOKEN) {
    try {
      fileBirdFolderCache = await loadFileBirdFolderTree();
      console.log(`[filebird] Loaded folder tree (${fileBirdFolderCache.size} folders known).\n`);
    } catch (err) {
      console.warn(`[filebird] Could not load folder tree — FileBird filing disabled for this run: ${err.message}\n`);
      fileBirdFolderCache = null;
    }
  } else {
    console.warn("[filebird] FILEBIRD_TOKEN not set — FileBird filing disabled for this run.\n");
  }

  let pageFolderCache = null;
  if (FILEBIRD_TOKEN) {
    try {
      pageFolderCache = await loadFileBirdPageFolderTree();
      console.log(`[filebird:pages] Loaded page folder tree (${pageFolderCache.size} folders known).\n`);
    } catch (err) {
      console.warn(`[filebird:pages] Could not load page folder tree — page folder filing disabled for this run: ${err.message}\n`);
    }
  }

  console.log("=== Syncing files (JSON data + scripts) ===");
  const filesResult = await syncFiles(fileBirdFolderCache);

  console.log("\n=== Syncing pages ===");
  const pagesResult = await syncPages(pageFolderCache);

  console.log("\n=== Summary ===");
  console.log(`Files:  ${filesResult.successCount} ok, ${filesResult.failCount} failed`);
  console.log(`Pages:  ${pagesResult.successCount} ok, ${pagesResult.failCount} failed`);

  if (filesResult.failCount > 0 || pagesResult.failCount > 0) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
