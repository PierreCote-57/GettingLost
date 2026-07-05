#!/usr/bin/env node
/**
 * sync.js
 *
 * Pushes this repo's content to WordPress, overwriting whatever is
 * currently live — no diffing, no confirmation prompt. This is the
 * "GitHub is master" sync: run it, and WordPress is made to match
 * the repo, full stop.
 *
 * Three kinds of targets:
 *
 *   1. PAGES — full-content overwrite via the WP REST API.
 *      Pages are discovered dynamically from WP (no page-map.json).
 *      New pages are auto-created when an HTML file exists in the
 *      repo with no matching WP page. Title, excerpt, featured
 *      image, and publish status are pushed from per-page JSON
 *      files under media/data/.
 *
 *   2. FILES (JSON data files + .jst scripts) — uploaded to the media
 *      library at /wp-content/uploads/<filename>. WordPress does NOT
 *      overwrite a same-named file by default (it silently appends
 *      "-1", "-2", etc. instead), so to get a true overwrite at the
 *      same URL this script:
 *        a. looks up the existing media item by filename
 *        b. deletes it (force=true, permanent — no trash)
 *        c. re-uploads a new media item with the same filename
 *
 *   3. GALLERY JSONs — auto-generated from per-page data files.
 *      Each gallery rule maps a folder path prefix to a gallery
 *      name. Only pages with published:true are included. Generated
 *      in memory and uploaded to WP — never written to the repo.
 *
 * Auth: WordPress Application Password (Basic Auth), provided via
 * the WP_USER and WP_APP_PASSWORD environment variables (GitHub
 * Secrets in the Action). Site URL via WP_SITE_URL.
 */

const fs = require("fs");
const path = require("path");

// ---------------------------------------------------------------------
// Top-level constants
// ---------------------------------------------------------------------

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const PAGES_ROOT = path.join(REPO_ROOT, "pages");
const POSTS_ROOT = path.join(REPO_ROOT, "posts");
const MEDIA_ROOT = path.join(REPO_ROOT, "media");
const DATA_ROOT = path.join(MEDIA_ROOT, "data");

const INCREMENTAL =
  process.argv.some((a) => a.startsWith("--changed-files=")) ||
  process.argv.some((a) => a.startsWith("--removed-files="));

const WP_SITE_URL = requireEnv("WP_SITE_URL").replace(/\/$/, "");
const WP_USER = requireEnv("WP_USER");
const WP_APP_PASSWORD = requireEnv("WP_APP_PASSWORD");

const AUTH_HEADER =
  "Basic " + Buffer.from(`${WP_USER}:${WP_APP_PASSWORD}`).toString("base64");

const FILEBIRD_TOKEN = process.env.FILEBIRD_TOKEN || null;

const FALLBACK_FEATURED_IMAGE_ID = 1751;

const GALLERY_RULES = [
  { name: "Lakes", path: "destinations/lakes/" },
  { name: "Campgrounds", path: "destinations/campgrounds/" },
  { name: "Parks", path: "destinations/parks/" },
  { name: "RecSites", path: "destinations/rec-sites/" },
  { name: "Destinations", path: "destinations/" },
  { name: "VanHowTo", path: "van/howto/" },
  { name: "VanChecklist", path: "van/checklists/" },
];

// ---------------------------------------------------------------------
// Incremental mode
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
// Data loading — WP pages, per-page JSONs, WP media
// ---------------------------------------------------------------------

async function loadWpPageMap() {
  const map = new Map();
  let page = 1;
  while (true) {
    const res = await wpFetch(`/pages?per_page=100&page=${page}&status=any`);
    if (!res.ok) throw new Error(`page listing failed: HTTP ${res.status}`);
    const items = await res.json();
    for (const item of items) {
      map.set(item.slug, { id: item.id, status: item.status });
    }
    const totalPages = parseInt(res.headers.get("X-WP-TotalPages") || "1", 10);
    if (page >= totalPages) break;
    page++;
  }
  return map;
}

function loadPerPageDataMap() {
  const map = new Map();
  if (!fs.existsSync(DATA_ROOT)) return map;

  const entries = fs.readdirSync(DATA_ROOT, { recursive: true });
  for (const entry of entries) {
    if (!entry.endsWith(".json")) continue;
    const normalized = entry.split(path.sep).join("/");
    const slug = path.basename(normalized, ".json");
    const parentDir = path.basename(path.dirname(normalized));
    if (slug !== parentDir) continue;
    const fullPath = path.join(DATA_ROOT, entry);
    const data = JSON.parse(fs.readFileSync(fullPath, "utf8"));
    const repoPath = path.dirname(normalized);
    map.set(slug, { data, repoPath });
  }
  return map;
}

// Turn a bare image filename (e.g. "IMG_0795.jpg") from page/post data into
// its WordPress uploads path, matching how loadWpMediaMap keys the media map.
// This is a media-map lookup KEY, not a display URL — so it intentionally does
// NOT mirror gettinglost.jst's formatImageUrl, which now returns a Jetpack
// Photon (i0.wp.com) URL for on-the-fly resizing. Keep this a plain
// /wp-content/uploads/ path, or the featured-image media-id lookup breaks.
// Empty/missing input is never valid — callers guarantee a real filename —
// so it throws rather than manufacturing a broken "" value.
function formatImageUrl(filename) {
  if (!filename) {
    throw new Error(
      "formatImageUrl: empty/missing image filename — data bug; callers must pass a real filename."
    );
  }
  return "/wp-content/uploads/" + filename;
}

async function loadWpMediaMap() {
  const map = new Map();
  let page = 1;
  while (true) {
    const res = await wpFetch(`/media?per_page=100&page=${page}&media_type=image`);
    if (!res.ok) throw new Error(`media listing failed: HTTP ${res.status}`);
    const items = await res.json();
    for (const item of items) {
      if (!item.source_url) continue;
      try {
        const urlPath = new URL(item.source_url).pathname;
        map.set(urlPath, item.id);
      } catch {
        map.set(item.source_url, item.id);
      }
    }
    const totalPages = parseInt(res.headers.get("X-WP-TotalPages") || "1", 10);
    if (page >= totalPages) break;
    page++;
  }
  return map;
}

// ---------------------------------------------------------------------
// Gallery JSON generation
// ---------------------------------------------------------------------

function generateGalleryJsons(perPageDataMap) {
  const galleries = new Map();

  for (const rule of GALLERY_RULES) {
    const entries = [];

    for (const [slug, { data, repoPath }] of perPageDataMap) {
      if (!repoPath.startsWith(rule.path)) continue;
      if (data.published !== true) continue;

      entries.push({
        title: data.title || slug,
        slug,
        image: data.featuredImage ?? "under-construction.png",
        teaser: data.excerpt || "",
        tags: data.tags || [],
      });
    }

    entries.sort((a, b) => a.title.localeCompare(b.title));
    galleries.set(rule.name, entries);
  }

  return galleries;
}

async function syncGalleryJsons(galleries, fileBirdFolderCache) {
  let successCount = 0;
  let failCount = 0;

  for (const [name, entries] of galleries) {
    const filename = `${name}.json`;
    const fileBuffer = Buffer.from(JSON.stringify(entries, null, 2));
    const relSubPath = `data/shared/gallery/${filename}`;
    const mediaId = await syncOneFileToWordPress(relSubPath, filename, fileBuffer, "application/json");
    if (mediaId) {
      successCount++;
      if (fileBirdFolderCache) {
        await syncOneFileToFileBird(fileBirdFolderCache, mediaId, relSubPath);
      }
    } else {
      failCount++;
    }
  }

  return { successCount, failCount };
}

// ---------------------------------------------------------------------
// PAGES sync
// ---------------------------------------------------------------------

function buildPageFileMap() {
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

function buildPostFileMap() {
  const map = new Map();
  if (!fs.existsSync(POSTS_ROOT)) return map;

  const entries = fs.readdirSync(POSTS_ROOT);
  for (const entry of entries) {
    if (!entry.endsWith(".html")) continue;
    const slug = path.basename(entry, ".html");
    const filePath = path.join(POSTS_ROOT, entry);
    const relPath = path.posix.join("posts", entry);
    map.set(slug, { filePath, relPath });
  }
  return map;
}

async function loadWpPostMap() {
  const map = new Map();
  let page = 1;
  while (true) {
    const res = await wpFetch(`/posts?per_page=100&page=${page}&status=any`);
    if (!res.ok) throw new Error(`post listing failed: HTTP ${res.status}`);
    const items = await res.json();
    for (const item of items) {
      map.set(item.slug, { id: item.id, status: item.status });
    }
    const totalPages = parseInt(res.headers.get("X-WP-TotalPages") || "1", 10);
    if (page >= totalPages) break;
    page++;
  }
  return map;
}

async function syncPages(pageFolderCache, wpPageMap, perPageDataMap, wpMediaMap) {
  const pageFileMap = buildPageFileMap();

  let successCount = 0;
  let failCount = 0;

  for (const [slug, entry] of pageFileMap) {
    if (CHANGED && !CHANGED.files.has(entry.relPath)) {
      const pd = perPageDataMap.get(slug);
      const jsonRelPath = pd
        ? `media/data/${pd.repoPath}/${slug}.json`
        : null;
      if (!jsonRelPath || !CHANGED.files.has(jsonRelPath)) continue;
    }

    const content = fs.readFileSync(entry.filePath, "utf8");
    const pageData = perPageDataMap.get(slug)?.data || {};
    const wpPage = wpPageMap.get(slug);

    const body = { content };
    if (pageData.title) body.title = pageData.title;
    if (pageData.excerpt !== undefined) body.excerpt = pageData.excerpt || "";
    if (pageData.published !== undefined) {
      body.status = pageData.published ? "publish" : "draft";
    }
    // GitHub is master: always assert the featured image. A named image
    // resolves to its media id (or the under-construction fallback if not yet
    // uploaded); null/absent pushes 0 to actively clear any featured image WP
    // may still have. Otherwise "remove the featured image" couldn't be done
    // from the repo alone.
    if (pageData.featuredImage) {
      body.featured_media = (wpMediaMap && wpMediaMap.get(formatImageUrl(pageData.featuredImage))) || FALLBACK_FEATURED_IMAGE_ID;
    } else {
      body.featured_media = 0;
    }

    try {
      let pageId;
      if (wpPage) {
        pageId = wpPage.id;
        const res = await wpFetch(`/pages/${pageId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        if (!res.ok) {
          const text = await res.text();
          console.error(`[pages] FAILED update ${slug} (id ${pageId}): HTTP ${res.status} — ${text}`);
          failCount++;
          continue;
        }

        const data = await res.json();
        if (data._content_warnings) {
          console.warn(`[pages] ${slug} (id ${pageId}): saved with warnings:`, data._content_warnings);
        } else {
          console.log(`[pages] OK updated ${slug} (id ${pageId})`);
        }
      } else {
        body.slug = slug;
        body.comment_status = "closed";
        if (!body.status) body.status = "draft";

        const res = await wpFetch("/pages", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        if (!res.ok) {
          const text = await res.text();
          console.error(`[pages] FAILED create ${slug}: HTTP ${res.status} — ${text}`);
          failCount++;
          continue;
        }

        const data = await res.json();
        pageId = data.id;
        wpPageMap.set(slug, { id: pageId, status: data.status });
        console.log(`[pages] OK created ${slug} (id ${pageId}, status ${data.status})`);
      }

      await syncOnePageToFileBird(pageFolderCache, pageId, entry.relPath);
      successCount++;
    } catch (err) {
      console.error(`[pages] ERROR ${slug}:`, err.message);
      failCount++;
    }
  }

  return { successCount, failCount };
}

// ---------------------------------------------------------------------
// POSTS sync
// ---------------------------------------------------------------------

async function syncPosts(postFolderCache, wpPostMap, perPageDataMap, wpMediaMap) {
  const postFileMap = buildPostFileMap();

  let successCount = 0;
  let failCount = 0;

  for (const [slug, entry] of postFileMap) {
    if (CHANGED && !CHANGED.files.has(entry.relPath)) {
      const pd = perPageDataMap.get(slug);
      const jsonRelPath = pd
        ? `media/data/${pd.repoPath}/${slug}.json`
        : null;
      if (!jsonRelPath || !CHANGED.files.has(jsonRelPath)) continue;
    }

    const content = fs.readFileSync(entry.filePath, "utf8");
    const postData = perPageDataMap.get(slug)?.data || {};
    const wpPost = wpPostMap.get(slug);

    const body = { content };
    if (postData.title) body.title = postData.title;
    if (postData.excerpt !== undefined) body.excerpt = postData.excerpt || "";
    if (postData.date) body.date = postData.date;
    if (postData.published !== undefined) {
      body.status = postData.published ? "publish" : "draft";
    }
    // GitHub is master: always assert the featured image (see syncPages).
    // null/absent pushes 0 to clear any featured image WP may still have.
    if (postData.featuredImage) {
      body.featured_media = (wpMediaMap && wpMediaMap.get(formatImageUrl(postData.featuredImage))) || FALLBACK_FEATURED_IMAGE_ID;
    } else {
      body.featured_media = 0;
    }

    try {
      let postId;
      if (wpPost) {
        postId = wpPost.id;
        const res = await wpFetch(`/posts/${postId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        if (!res.ok) {
          const text = await res.text();
          console.error(`[posts] FAILED update ${slug} (id ${postId}): HTTP ${res.status} — ${text}`);
          failCount++;
          continue;
        }

        const data = await res.json();
        if (data._content_warnings) {
          console.warn(`[posts] ${slug} (id ${postId}): saved with warnings:`, data._content_warnings);
        } else {
          console.log(`[posts] OK updated ${slug} (id ${postId})`);
        }
      } else {
        body.slug = slug;
        body.comment_status = "open";
        if (!body.status) body.status = "draft";

        const res = await wpFetch("/posts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        if (!res.ok) {
          const text = await res.text();
          console.error(`[posts] FAILED create ${slug}: HTTP ${res.status} — ${text}`);
          failCount++;
          continue;
        }

        const data = await res.json();
        postId = data.id;
        wpPostMap.set(slug, { id: postId, status: data.status });
        console.log(`[posts] OK created ${slug} (id ${postId}, status ${data.status})`);
      }

      await syncOnePageToFileBird(postFolderCache, postId, entry.relPath);
      successCount++;
    } catch (err) {
      console.error(`[posts] ERROR ${slug}:`, err.message);
      failCount++;
    }
  }

  return { successCount, failCount };
}

// ---------------------------------------------------------------------
// FILES sync (JSON data files + .jst scripts) — delete-then-recreate
// ---------------------------------------------------------------------

function guessMimeFromExt(filename) {
  if (filename.endsWith(".jst")) return "text/text";
  if (filename.endsWith(".cst")) return "text/css";
  if (filename.endsWith(".json")) return "application/json";
  return "application/octet-stream";
}

async function findExistingMediaIdByFilename(filename) {
  const titleGuess = filename.replace(/\.(json|jst|cst)$/, "");
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
// FILEBIRD folder filing
// ---------------------------------------------------------------------

async function loadFileBirdFolderTree() {
  const cache = new Map();
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
      console.log(`[filebird:media] created folder "${pathSoFar}" (id ${newId})`);
    }

    parentId = folderCache.get(cacheKey);
  }

  return parentId;
}

async function syncOneFileToFileBird(folderCache, mediaId, relSubPath) {
  if (!folderCache) return;

  const segments = path.posix.dirname(relSubPath).split("/").filter(Boolean);
  if (segments.length === 0) return;

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
    console.log(`[filebird:media] filed ${relSubPath} -> ${segments.join("/")}`);
  } catch (err) {
    console.warn(`[filebird:media] FAILED to file ${relSubPath}:`, err.message);
  }
}

// ---------------------------------------------------------------------
// FILEBIRD PAGE FOLDER filing
// ---------------------------------------------------------------------

async function loadFileBirdPageFolderTree() {
  const cache = new Map();
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

  const afterPages = relPath.startsWith("pages/") ? relPath.slice("pages/".length) : relPath;
  const segments = path.posix.dirname(afterPages).split("/").filter((s) => s && s !== ".");
  if (segments.length === 0) return;

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
  const filenames = allEntries.filter((f) => f.endsWith(".json") || f.endsWith(".jst") || f.endsWith(".cst"));

  for (const relSubPath of filenames) {
    const normalized = relSubPath.split(path.sep).join("/");

    // Skip gallery index JSONs — auto-generated by generateGalleryJsons()
    if (normalized.startsWith("data/shared/gallery/") && normalized.endsWith(".json")) {
      continue;
    }

    const filePath = path.join(MEDIA_ROOT, relSubPath);
    const filename = path.basename(filePath);
    const relPath = path.posix.relative(REPO_ROOT, filePath);

    if (CHANGED && !CHANGED.files.has(relPath)) {
      continue;
    }

    const fileBuffer = fs.readFileSync(filePath);
    const mimeType = guessMimeFromExt(filename);

    const mediaId = await syncOneFileToWordPress(normalized, filename, fileBuffer, mimeType);

    if (mediaId) {
      successCount++;
      await syncOneFileToFileBird(fileBirdFolderCache, mediaId, normalized);
    } else {
      failCount++;
    }
  }

  return { successCount, failCount };
}

// ---------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------

async function main() {
  console.log(`Syncing to ${WP_SITE_URL} ...\n`);

  let fileBirdFolderCache = null;
  if (FILEBIRD_TOKEN) {
    try {
      fileBirdFolderCache = await loadFileBirdFolderTree();
      console.log(`[filebird:media] Loaded folder tree (${fileBirdFolderCache.size} folders known).\n`);
    } catch (err) {
      console.warn(`[filebird:media] Could not load folder tree — FileBird filing disabled for this run: ${err.message}\n`);
    }
  } else {
    console.warn("[filebird:media] FILEBIRD_TOKEN not set — FileBird filing disabled for this run.\n");
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

  console.log("=== Loading data maps ===");
  const perPageDataMap = loadPerPageDataMap();
  console.log(`[data] Loaded ${perPageDataMap.size} per-page data files.`);

  const wpPageMap = await loadWpPageMap();
  console.log(`[wp] Loaded ${wpPageMap.size} existing WP pages.`);

  const wpPostMap = await loadWpPostMap();
  console.log(`[wp] Loaded ${wpPostMap.size} existing WP posts.`);

  const wpMediaMap = await loadWpMediaMap();
  console.log(`[wp] Loaded ${wpMediaMap.size} media attachments.\n`);

  console.log("=== Generating gallery JSONs ===");
  const galleries = generateGalleryJsons(perPageDataMap);
  for (const [name, entries] of galleries) {
    console.log(`[gallery] ${name}.json: ${entries.length} entries`);
  }

  console.log("\n=== Syncing files (JSON data + scripts) ===");
  const filesResult = await syncFiles(fileBirdFolderCache);

  console.log("\n=== Syncing gallery JSONs ===");
  const galleryResult = await syncGalleryJsons(galleries, fileBirdFolderCache);

  console.log("\n=== Syncing pages ===");
  const pagesResult = await syncPages(pageFolderCache, wpPageMap, perPageDataMap, wpMediaMap);

  console.log("\n=== Syncing posts ===");
  const postsResult = await syncPosts(pageFolderCache, wpPostMap, perPageDataMap, wpMediaMap);

  console.log("\n=== Summary ===");
  console.log(`Files:     ${filesResult.successCount} ok, ${filesResult.failCount} failed`);
  console.log(`Galleries: ${galleryResult.successCount} ok, ${galleryResult.failCount} failed`);
  console.log(`Pages:     ${pagesResult.successCount} ok, ${pagesResult.failCount} failed`);
  console.log(`Posts:     ${postsResult.successCount} ok, ${postsResult.failCount} failed`);

  const totalFails = filesResult.failCount + galleryResult.failCount + pagesResult.failCount + postsResult.failCount;
  if (totalFails > 0) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
