#!/usr/bin/env node
/**
 * sync.js, a github-action-based WordPress sync script.
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

// Prefix every log line with a PDT wall-clock timestamp (HH:MM:SS.mmm, no zone
// label), applied once here so no call site has to. On a long run the stamps let
// you validate progress and spot where time is being spent (e.g. a slow phase
// between two lines).
for (const m of ["log", "warn", "error"]) {
  const orig = console[m];
  console[m] = (...a) =>
    orig(
      `[${new Date().toLocaleTimeString("en-GB", { timeZone: "America/Los_Angeles", hour: "2-digit", minute: "2-digit", second: "2-digit", fractionalSecondDigits: 3, hour12: false })}]`,
      ...a
    );
}

// ---------------------------------------------------------------------
// Top-level constants
// ---------------------------------------------------------------------

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const PAGES_ROOT = path.join(REPO_ROOT, "pages");
const POSTS_ROOT = path.join(REPO_ROOT, "posts");
const MEDIA_ROOT = path.join(REPO_ROOT, "media");
const DATA_ROOT = path.join(MEDIA_ROOT, "data");
const LOGS_ROOT = path.join(REPO_ROOT, "logs");

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

// Leg types that may be AUTHORED in a page's access.legs. The drive list is
// ordered easiest -> hardest and doubles as the severity rank; it mirrors
// GL.ROAD_RANK in gl-constants.jst (browser code, can't be required here, so
// keep the two in sync).
//
// pavement and back_country are absent because neither is ever authored:
// pavement is derived from legs: [] — pavement segments are excluded from legs
// altogether — and back_country is derived from any non-drive leg. unpaved is
// a measured non-paved tail whose character is not yet refined; it ranks
// mildest so that any known type outranks it and takes the badge.
//
// Non-drive legs have no rank — any one of them means you leave the van, which
// is the whole distinction.
const DRIVE_LEG_TYPES = ["unpaved", "dirt", "potholes", "sharp_rock", "rugged"];
const NON_DRIVE_LEG_TYPES = ["walk", "hike", "boat"];
const LEG_TYPES = [...DRIVE_LEG_TYPES, ...NON_DRIVE_LEG_TYPES];

// What KIND of place a destination is, carried as `tags.types`. Mirrors
// GL.DESTINATION_TYPES in gl-constants.jst (browser code, can't be required here,
// so keep the two in sync). Alphabetical: unlike the leg types above, the order
// carries no meaning.
//
// A type is never mandatory — validateTypes checks the VALUE, never the presence.
// An untyped destination is a legitimate state, and the one that keeps `park`
// meaningful: a city park carries no type rather than the wrong one.
const DESTINATION_TYPES = ["campground", "lake", "park", "rec-site"];

// What a link IS, carried as `type` on a `links[]` entry. Mirrors GL.LINK_TYPES
// in gl-constants.jst — keep the two in sync. Optional in the same way and for
// the same reason as DESTINATION_TYPES: a link that is none of these keeps its
// label and carries no type, so validateLinks checks the VALUE, never presence.
const LINK_TYPES = ["homepage", "map", "reservation"];

// Validate every page's access.legs against the authorable vocabulary. Build-time
// DATA check only — the road badge itself is derived in the browser
// (gettinglost.jst). A page FAILS if any leg is invalid: an unknown type, or an
// `unpaved` leg with no positive km (unpaved asserts a MEASURED tail, so it means
// nothing without one). Pages with no legs (e.g. lakes) are not applicable and
// aren't counted either way.
//
// One of the checks in main()'s validate block: each bad leg is annotated
// (::error::) as it is found, the tally line closes the check, and the returned
// invalid count is what stops the run before anything is pushed.
function validateLegs(perPageDataMap) {
  let checked = 0;
  let invalid = 0;
  for (const [key, pd] of perPageDataMap) {
    const legs = pd.data && pd.data.access && pd.data.access.legs;
    if (!Array.isArray(legs) || legs.length === 0) continue;
    checked++;
    let bad = false;
    for (const leg of legs) {
      const type = leg && leg.type;
      if (!LEG_TYPES.includes(type)) {
        annotateFailure(`  ${key}: unknown leg type "${type}".`);
        bad = true;
      } else if (type === "unpaved" && !(typeof leg.km === "number" && leg.km > 0)) {
        annotateFailure(`  ${key}: unpaved leg has no km — unpaved states a measured tail, meaningless without one.`);
        bad = true;
      }
    }
    if (bad) invalid++;
  }
  console.log(`Legs:  ${checked} checked, ${invalid} invalid`);
  return invalid;
}

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

  // A change under local/ is a change to the sync ENGINE/config, not to content.
  // Most such changes (logging, refactors, hydration/gallery structure) don't
  // require re-pushing existing content, so we no longer force a full sync — we
  // just WARN. The narrow exception is a change to the page/post TRANSFORM logic
  // (featured_media resolution, wpSettings→status mapping, slug derivation,
  // formatImageUrl): that affects already-synced pages whose files didn't change,
  // and incremental mode will skip them. When you make one of those, run sync.yml
  // manually. (The hydrated lists + PageMap run unconditionally every push, so
  // page-data-derived outputs stay fresh regardless.)
  const localChanged = changedList.some((f) => f.startsWith("local/"));

  if (localChanged) {
    console.warn(
      "[incremental] A file under local/ changed (sync engine/config) — running INCREMENTAL only.\n" +
        "  If this was a transform-logic change (pages/posts featured_media/status/slug/image URL),\n" +
        "  run the full sync (sync.yml) manually, or the affected pages will stay stale on WP."
    );
  }

  CHANGED = { files: new Set(changedList) };
  console.log(`[incremental] Running in incremental mode — ${CHANGED.files.size} changed file(s).`);
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
// Slug helpers — universal "<base>_<ext>" WP slug format
// ---------------------------------------------------------------------
// Every object we push to WP (page, post, attachment) gets a slug of the form
// "<base>_<ext>" so nothing shares the post-slug namespace with anything else:
//   beavertail-lake.html -> beavertail-lake_html
//   beavertail-lake.json -> beavertail-lake_json
// The data FILE keeps its plain name (beavertail-lake.json, fetched by URL);
// only the attachment's post_name carries the _json. WP lowercases + sanitises
// slugs, so we pre-sanitise to what WP will store — otherwise the
// requested-vs-actual validation below would false-flag.

function sanitizeSlug(s) {
  return String(s)
    .toLowerCase()
    .replace(/[^a-z0-9 _-]/g, "") // drop chars WP drops (e.g. ".")
    .trim()
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-");
}

// The one universal rule: filename -> slug. Replace the last "." with "_",
// then sanitise to what WP will store. Used for pages, posts, AND media —
// the github filename is the master and the sole source of a slug. No
// extension is assumed.
//   amor-lake.html -> amor-lake_html      foo.bar -> foo_bar
function fileToSlug(filename) {
  const ext = path.extname(filename).replace(/^\./, "").toLowerCase();
  const base = path.basename(filename, path.extname(filename));
  return sanitizeSlug(`${base}_${ext}`);
}

// The inverse: slug -> filename. Replace the last "_" with ".". Lets a map
// keyed by filename be looked up from a WP object's slug.
//   amor-lake_html -> amor-lake.html      foo_bar -> foo.bar
function slugToFilename(slug) {
  const i = slug.lastIndexOf("_");
  return i === -1 ? slug : `${slug.slice(0, i)}.${slug.slice(i + 1)}`;
}

// Extract the slug WP actually assigned, from a permalink. Authoritative —
// unlike a create response's `slug`, which can echo the requested value while
// WP silently stored a "-2" suffix.
function slugFromLink(link) {
  try {
    const parts = new URL(link).pathname.split("/").filter(Boolean);
    return parts.length ? parts[parts.length - 1] : "";
  } catch (_) {
    return "";
  }
}

// A slug/filename drift means WP did NOT store what we asked for. That's a
// failure, not a warning: emit a GitHub Actions error annotation (shows on the
// run summary) so it can't be missed. Callers must ALSO count it (failCount++ /
// return null) so the job actually goes red.
function annotateFailure(message) {
  console.log(`::error::${message}`);
}

// A bad-but-recoverable data value (e.g. an unknown road condition): emit a
// GitHub Actions warning annotation so it shows on the run summary without
// failing the job. Callers also console.warn and drop the offending value.
function annotateWarning(message) {
  console.log(`::warning::${message}`);
}

// ---------------------------------------------------------------------
// wpSettings — GitHub-mastered per-object WordPress settings
// ---------------------------------------------------------------------
// Each page/post data file carries a `wpSettings` block:
//   { "published": <bool>, "comments": "open" | "closed" }
// published -> WP status:         true "publish" / false "draft"
//              (absent -> undefined; create then falls back to "draft").
// comments  -> WP comment_status: passed through; DEFAULT "open" when absent
//              (only an explicit "closed" turns them off). Asserted on every
//              create AND update so the repo always wins (like featured_media).

function wpStatusFromData(data) {
  const pub = data.wpSettings ? data.wpSettings.published : undefined;
  return pub === undefined ? undefined : (pub ? "publish" : "draft");
}

function wpCommentStatusFromData(data) {
  const c = data.wpSettings ? data.wpSettings.comments : undefined;
  return c === "closed" ? "closed" : "open";
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
      map.set(slugToFilename(item.slug), { id: item.id, status: item.status });
    }
    const totalPages = parseInt(res.headers.get("X-WP-TotalPages") || "1", 10);
    if (page >= totalPages) break;
    page++;
  }
  console.log(`[wp] Loaded ${map.size} existing WP pages.`);
  return map;
}

function loadPerPageDataMap() {
  const map = new Map();
  const entries = fs.existsSync(DATA_ROOT) ? fs.readdirSync(DATA_ROOT, { recursive: true }) : [];
  for (const entry of entries) {
    if (!entry.endsWith(".json")) continue;
    const normalized = entry.split(path.sep).join("/");
    const filename = path.basename(normalized); // amor-lake.json — the key
    const base = path.basename(normalized, ".json");
    const parentDir = path.basename(path.dirname(normalized));
    if (base !== parentDir) continue;
    const fullPath = path.join(DATA_ROOT, entry);
    const data = JSON.parse(fs.readFileSync(fullPath, "utf8"));
    const repoPath = path.dirname(normalized);
    map.set(filename, { data, repoPath });
  }
  console.log(`[data] Loaded ${map.size} per-page data files.`);
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
  console.log(`[wp] Loaded ${map.size} media attachments.\n`);
  return map;
}

// ---------------------------------------------------------------------
// PageMap generation
// ---------------------------------------------------------------------

// Driven by the PAGE files (keyed by filename — the master). Each page's data is
// its "<base>.json" — constructed from the page filename, never looked up by
// base. The emitted `file` is the master; the consumer (gettinglost.jst) derives
// the URL slug from it via fileToSlug.
function generatePageMap(ghPageMap, perPageDataMap) {
  const map = {};
  for (const [filename] of ghPageMap) {
    const base = path.basename(filename, path.extname(filename));
    const pd = perPageDataMap.get(`${base}.json`);
    if (!pd || wpStatusFromData(pd.data) !== "publish") continue;
    map[filename] = { name: pd.data.name || base };
  }
  console.log(`[pageMap] PageMap.json: ${Object.keys(map).length} entries`);
  return map;
}

async function syncPageMap(glPageMap, fileBirdFolderCache) {
  console.log("\n=== Syncing PageMap ===");
  let successCount = 0;
  let failCount = 0;

  // PageMap.json — slug-to-metadata lookup for cross-page references
  const pmBuffer = Buffer.from(JSON.stringify(glPageMap, null, 2));
  const pmRelPath = "data/shared/gallery/PageMap.json";
  const pmId = await syncOneFileToWordPress(pmRelPath, "PageMap.json", pmBuffer, "application/json");
  if (pmId) {
    successCount++;
    if (fileBirdFolderCache) {
      await syncOneFileToFileBird(fileBirdFolderCache, pmId, pmRelPath);
    }
  } else {
    failCount++;
  }

  return { successCount, failCount };
}

// ---------------------------------------------------------------------
// PAGES sync
// ---------------------------------------------------------------------

// Map of page/post source files, keyed by FILENAME — the source of truth.
// Discovery is generic: every non-hidden regular file under the root, with
// no extension assumed. The slug is derived from the filename via fileToSlug;
// the base (filename minus its own extension) is only used to locate the
// page's data file (<base>.json).
function buildFileMap(root, repoPrefix) {
  const map = new Map();
  if (!fs.existsSync(root)) return map;

  for (const entry of fs.readdirSync(root, { recursive: true })) {
    const filename = path.basename(entry);
    if (filename.startsWith(".")) continue; // skip .DS_Store and the like
    const filePath = path.join(root, entry);
    if (!fs.statSync(filePath).isFile()) continue; // skip directories
    const relPath = path.posix.join(repoPrefix, entry.split(path.sep).join("/"));
    map.set(filename, { filePath, relPath });
  }
  return map;
}

function buildGhPageMap() {
  const ghPageMap = buildFileMap(PAGES_ROOT, "pages");
  return ghPageMap;
}

function buildGhPostMap() {
  const ghPostMap = buildFileMap(POSTS_ROOT, "posts");
  return ghPostMap;
}

async function loadWpPostMap() {
  const map = new Map();
  let page = 1;
  while (true) {
    const res = await wpFetch(`/posts?per_page=100&page=${page}&status=any`);
    if (!res.ok) throw new Error(`post listing failed: HTTP ${res.status}`);
    const items = await res.json();
    for (const item of items) {
      map.set(slugToFilename(item.slug), { id: item.id, status: item.status });
    }
    const totalPages = parseInt(res.headers.get("X-WP-TotalPages") || "1", 10);
    if (page >= totalPages) break;
    page++;
  }
  console.log(`[wp] Loaded ${map.size} existing WP posts.`);
  return map;
}

async function syncPages(pageFolderCache, ghPageMap, wpPageMap, perPageDataMap, wpMediaMap) {
  console.log("\n=== Syncing pages ===");
  let successCount = 0;
  let failCount = 0;

  for (const [filename, entry] of ghPageMap) {
    const base = path.basename(filename, path.extname(filename));
    if (CHANGED && !CHANGED.files.has(entry.relPath)) {
      const pd = perPageDataMap.get(`${base}.json`);
      const jsonRelPath = pd
        ? `media/data/${pd.repoPath}/${base}.json`
        : null;
      if (!jsonRelPath || !CHANGED.files.has(jsonRelPath)) continue;
    }

    const content = fs.readFileSync(entry.filePath, "utf8");
    const pageData = perPageDataMap.get(`${base}.json`)?.data || {};
    const wpSlug = fileToSlug(filename);
    const wpPage = wpPageMap.get(filename);

    const body = { content };
    if (pageData.name) body.title = pageData.name;
    if (pageData.excerpt !== undefined) body.excerpt = pageData.excerpt || "";
    const pageStatus = wpStatusFromData(pageData);
    if (pageStatus !== undefined) body.status = pageStatus;
    // GitHub is master: assert comment_status on every create AND update
    // (default "open"; only an explicit wpSettings.comments="closed" turns it off).
    body.comment_status = wpCommentStatusFromData(pageData);
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
          console.error(`[pages] FAILED update ${filename} (id ${pageId}): HTTP ${res.status} — ${text}`);
          failCount++;
          continue;
        }

        const data = await res.json();
        const actualSlug = slugFromLink(data.link) || data.slug;
        if (data._content_warnings) {
          console.warn(`[pages] ${wpSlug} (id ${pageId}): saved with warnings:`, data._content_warnings);
        } else {
          console.log(`[pages] OK updated "${wpSlug}" (id ${pageId}, actual slug "${actualSlug}")`);
        }
        if (actualSlug !== wpSlug) {
          annotateFailure(`[pages] SLUG MISMATCH on update: id ${pageId} is stored as "${actualSlug}", expected "${wpSlug}".`);
          failCount++;
          continue;
        }
      } else {
        body.slug = wpSlug;
        if (!body.status) body.status = "draft";

        const res = await wpFetch("/pages", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        if (!res.ok) {
          const text = await res.text();
          console.error(`[pages] FAILED create ${filename}: HTTP ${res.status} — ${text}`);
          failCount++;
          continue;
        }

        const data = await res.json();
        pageId = data.id;
        const actualSlug = slugFromLink(data.link) || data.slug;
        wpPageMap.set(slugToFilename(actualSlug), { id: pageId, status: data.status });
        console.log(`[pages] OK created "${wpSlug}" → id ${pageId}, actual slug "${actualSlug}" (link ${data.link}), status ${data.status}`);
        if (actualSlug !== wpSlug) {
          annotateFailure(`[pages] SLUG DRIFT: requested "${wpSlug}" but WP stored "${actualSlug}" — slug reserved (duplicate/trash).`);
          failCount++;
          continue;
        }
      }

      await syncOnePageToFileBird(pageFolderCache, pageId, entry.relPath);
      successCount++;
    } catch (err) {
      console.error(`[pages] ERROR ${filename}:`, err.message);
      failCount++;
    }
  }

  return { successCount, failCount };
}

// ---------------------------------------------------------------------
// POSTS sync
// ---------------------------------------------------------------------

async function syncPosts(postFolderCache, ghPostMap, wpPostMap, perPageDataMap, wpMediaMap) {
  console.log("\n=== Syncing posts ===");
  let successCount = 0;
  let failCount = 0;

  for (const [filename, entry] of ghPostMap) {
    const base = path.basename(filename, path.extname(filename));
    if (CHANGED && !CHANGED.files.has(entry.relPath)) {
      const pd = perPageDataMap.get(`${base}.json`);
      const jsonRelPath = pd
        ? `media/data/${pd.repoPath}/${base}.json`
        : null;
      if (!jsonRelPath || !CHANGED.files.has(jsonRelPath)) continue;
    }

    const content = fs.readFileSync(entry.filePath, "utf8");
    const postData = perPageDataMap.get(`${base}.json`)?.data || {};
    const wpSlug = fileToSlug(filename);
    const wpPost = wpPostMap.get(filename);

    const body = { content };
    if (postData.name) body.title = postData.name;
    if (postData.excerpt !== undefined) body.excerpt = postData.excerpt || "";
    if (postData.date) body.date = postData.date;
    const postStatus = wpStatusFromData(postData);
    if (postStatus !== undefined) body.status = postStatus;
    // GitHub is master: assert comment_status on every create AND update
    // (default "open"; only an explicit wpSettings.comments="closed" turns it off).
    body.comment_status = wpCommentStatusFromData(postData);
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
          console.error(`[posts] FAILED update ${filename} (id ${postId}): HTTP ${res.status} — ${text}`);
          failCount++;
          continue;
        }

        const data = await res.json();
        const actualSlug = slugFromLink(data.link) || data.slug;
        if (data._content_warnings) {
          console.warn(`[posts] ${wpSlug} (id ${postId}): saved with warnings:`, data._content_warnings);
        } else {
          console.log(`[posts] OK updated "${wpSlug}" (id ${postId}, actual slug "${actualSlug}")`);
        }
        if (actualSlug !== wpSlug) {
          annotateFailure(`[posts] SLUG MISMATCH on update: id ${postId} is stored as "${actualSlug}", expected "${wpSlug}".`);
          failCount++;
          continue;
        }
      } else {
        body.slug = wpSlug;
        if (!body.status) body.status = "draft";

        const res = await wpFetch("/posts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        if (!res.ok) {
          const text = await res.text();
          console.error(`[posts] FAILED create ${filename}: HTTP ${res.status} — ${text}`);
          failCount++;
          continue;
        }

        const data = await res.json();
        postId = data.id;
        const actualSlug = slugFromLink(data.link) || data.slug;
        wpPostMap.set(slugToFilename(actualSlug), { id: postId, status: data.status });
        console.log(`[posts] OK created "${wpSlug}" → id ${postId}, actual slug "${actualSlug}" (link ${data.link}), status ${data.status}`);
        if (actualSlug !== wpSlug) {
          annotateFailure(`[posts] SLUG DRIFT: requested "${wpSlug}" but WP stored "${actualSlug}" — slug reserved (duplicate/trash).`);
          failCount++;
          continue;
        }
      }

      await syncOnePageToFileBird(postFolderCache, postId, entry.relPath);
      successCount++;
    } catch (err) {
      console.error(`[posts] ERROR ${filename}:`, err.message);
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
  if (filename.endsWith(".pdf")) return "application/pdf";
  return "application/octet-stream";
}

async function findExistingMediaIdByFilename(filename) {
  const titleGuess = filename.replace(/\.(json|jst|cst|pdf)$/, "");
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

async function uploadMedia(filename, fileBuffer, mimeType, desiredSlug) {
  const qs = desiredSlug ? `?slug=${encodeURIComponent(desiredSlug)}` : "";
  const res = await wpFetch(`/media${qs}`, {
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

// Force an attachment's slug via a follow-up update — used when the binary
// create ignores the ?slug= query parameter.
async function setMediaSlug(id, desiredSlug) {
  const res = await wpFetch(`/media/${id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ slug: desiredSlug }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`slug update failed: HTTP ${res.status} — ${body}`);
  }
  return res.json();
}

async function syncOneFileToWordPress(relSubPath, filename, fileBuffer, mimeType) {
  try {
    const desiredSlug = fileToSlug(filename);
    const existingId = await findExistingMediaIdByFilename(filename);
    if (existingId) {
      await deleteMedia(existingId);
    }
    let uploaded = await uploadMedia(filename, fileBuffer, mimeType, desiredSlug);

    // The binary create may ignore ?slug=. If the slug didn't take, force it
    // with a follow-up update so the attachment lands on "<base>_<ext>".
    if (uploaded.slug !== desiredSlug) {
      console.warn(`[files] ${relSubPath}: slug on create was "${uploaded.slug}", requested "${desiredSlug}" — applying follow-up update.`);
      try {
        uploaded = await setMediaSlug(uploaded.id, desiredSlug);
      } catch (e) {
        console.error(`[files] ${relSubPath}: follow-up slug update FAILED: ${e.message}`);
      }
    }

    // Validate: WP must have stored the slug and filename we asked for.
    if (uploaded.slug !== desiredSlug) {
      annotateFailure(`[files] SLUG MISMATCH ${relSubPath}: requested "${desiredSlug}", WP stored "${uploaded.slug}".`);
      return null;
    }
    if (!(typeof uploaded.source_url === "string" && uploaded.source_url.endsWith(`/${filename}`))) {
      annotateFailure(`[files] FILENAME MISMATCH ${relSubPath}: expected .../${filename}, WP stored "${uploaded.source_url}".`);
      return null;
    }

    console.log(`[files] OK ${relSubPath}${existingId ? " (overwritten)" : " (new)"} — id ${uploaded.id}, slug "${uploaded.slug}", url ${uploaded.source_url}`);
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

// The manifest (list_browser/datasets.json) is the single source of truth for
// which files get HYDRATED at sync time: each entry's `file` is a pointer/inline
// list whose `{file}` pointers are replaced with the referenced page's JSON.
// The manifest itself is published by syncHydratedLists() too, carrying the counts
// collected from the hydrated rows, so the repo copy and the published copy
// differ. list_browser.json isn't listed there and copies verbatim like any other
// file.
const LIST_BROWSER_DIR = "data/shared/list_browser";
const MANIFEST_REL = `${LIST_BROWSER_DIR}/datasets.json`;

// The parsed manifest entries: { id, file, title, options }.
function loadDatasetManifest() {
  const datasets = JSON.parse(fs.readFileSync(path.join(MEDIA_ROOT, MANIFEST_REL), "utf8"));
  return datasets;
}

// Everything syncFiles() must NOT copy verbatim — the hydrated dataset files
// plus the manifest, all published by syncHydratedLists() instead.
function buildExcludedSet(datasets) {
  const excluded = new Set(datasets.map((d) => `${LIST_BROWSER_DIR}/${d.file}`));
  excluded.add(MANIFEST_REL);
  return excluded;
}

// The road badge a row's access derives. Mirrors GL.deriveRoadBadge in
// gettinglost.jst, which owns the render-time derivation; this copy exists only
// to COUNT rows per badge. It trusts what it reads because validateLegs already
// failed the build on an unknown leg type or an unmeasured `unpaved`.
// null means no badge at all — the row's road is unmeasured.
function deriveRoad(access) {
  const legs = access && access.legs;
  if (!Array.isArray(legs)) return null;
  if (legs.length === 0) return "pavement";

  let worst = -1;
  for (const leg of legs) {
    const type = leg && leg.type;
    if (NON_DRIVE_LEG_TYPES.includes(type)) return "back_country";
    const rank = DRIVE_LEG_TYPES.indexOf(type);
    if (rank > worst) worst = rank;
  }
  return worst < 0 ? null : DRIVE_LEG_TYPES[worst];
}

// Add one row's values to a facet's count map. The Set is what makes this one
// count per ROW: a row listing a value twice would still be kept once by the
// filter, so it must count once here.
function countRowValues(map, values) {
  for (const value of new Set(values)) {
    map[value] = (map[value] || 0) + 1;
  }
}

// How many rows each filter value would match, per facet, across one hydrated
// dataset — collected here so the browser reads finished numbers instead of
// walking the rows itself.
//
// `keywords` is the OPEN vocabulary: its keys ARE the choice list the keyword
// filter offers, which is why they are sorted. `types`, `badges` and `access` are
// CLOSED vocabularies the browser already holds (GL.DESTINATION_TYPES,
// GL.TAG_COLORS, GL.ROAD_COLORS); only the numbers come from here, so a value
// nobody used simply has no key and the browser reads it as 0 — a closed
// vocabulary advertising room not yet used.
//
// `types` gets no bucket for untyped rows: a row with no type matches no type
// filter, so it is simply absent and these counts sum to less than the row count.
// (`access` is the opposite — see below.)
//
// `access` counts the DERIVED road badge, with unmeasured rows under "unknown"
// (never a road value, so it cannot collide). The access control is a threshold
// and an unmeasured road passes every one of them, so the browser adds those
// rows into every option's running total.
function collectCounts(hydratedRows) {
  const keywords = {};
  const types = {};
  const badges = {};
  const access = {};

  for (const row of hydratedRows) {
    const tags = row.tags || {};
    countRowValues(keywords, tags.keywords || []);
    countRowValues(types, tags.types || []);
    countRowValues(badges, tags.badges || []);
    countRowValues(access, [deriveRoad(row.access) || "unknown"]);
  }

  const sortedKeywords = {};
  for (const keyword of Object.keys(keywords).sort()) {
    sortedKeywords[keyword] = keywords[keyword];
  }

  const counts = { keywords: sortedKeywords, types, badges, access };
  return counts;
}

// Replace each `{file}` pointer entry with the referenced page's JSON, matching
// the gallery merge ({ ...pageData, file }). Inline entries (no `file`) pass
// through untouched. An unresolvable pointer is a hard failure, and the entry is
// skipped so no partial list can be published. `perPageDataMap` is keyed by
// `<base>.json` (see loadPerPageDataMap).
//
// Problems are RETURNED, not printed: validateLists() owns the reporting, so every
// failure line lands under the validate block's header instead of during the load.
function hydrateList(entries, relPath, perPageDataMap) {
  const problems = [];
  const hydrated = [];
  for (const entry of entries) {
    if (entry && entry.file) {
      const base = path.basename(entry.file, path.extname(entry.file));
      const pd = perPageDataMap.get(`${base}.json`);
      if (!pd) {
        problems.push(`${relPath}: unresolvable file pointer "${entry.file}" — no page data found.`);
        continue;
      }
      hydrated.push({ ...pd.data, file: entry.file });
    } else {
      hydrated.push(entry);
    }
  }
  return { hydrated, problems };
}

// Read every manifest-listed dataset file and hydrate it. This is DERIVING what
// gets published — the file's content decides the output — so it belongs in the
// load phase, where the validate block can inspect the result before anything is
// pushed. The counts ride along for the same reason: by the time the push phase
// runs, every byte it will upload is already decided.
//
// Contrast with a plain file copy, which reads at upload time and stays there: the
// bytes are the payload of a decision already made, and hoisting them would mean
// holding every image in memory for the whole run.
function loadHydratedListSet(datasets, perPageDataMap) {
  const hydratedSets = [];

  for (const dataset of datasets) {
    const relPath = `${LIST_BROWSER_DIR}/${dataset.file}`;
    const filePath = path.join(MEDIA_ROOT, relPath);

    let entries;
    try {
      entries = JSON.parse(fs.readFileSync(filePath, "utf8"));
    } catch (err) {
      hydratedSets.push({ dataset, relPath, hydrated: [], counts: null, problems: [`${relPath}: could not parse JSON — ${err.message}`] });
      continue;
    }

    const { hydrated, problems } = hydrateList(entries, relPath, perPageDataMap);
    hydratedSets.push({ dataset, relPath, hydrated, counts: collectCounts(hydrated), problems });
  }

  return hydratedSets;
}

// Every `tags.types` value across the hydrated rows is in the vocabulary. One of
// the checks in main()'s validate block.
//
// VOCABULARY ONLY, never presence: a row with no types is correct, not missing
// something. A row typed outside the list is the error — it would sit in the data
// answering no filter, invisible, with nothing on screen to say why.
//
// It runs over the HYDRATED rows because that is the only place both kinds are
// visible: per-page rows resolved from `{file}` pointers, and the inline rows that
// exist nowhere but the dataset file. perPageDataMap would miss 98 of 116.
function validateTypes(hydratedSets) {
  let checked = 0;
  let invalid = 0;

  for (const set of hydratedSets) {
    for (const row of set.hydrated) {
      const types = (row.tags || {}).types;
      if (!Array.isArray(types) || types.length === 0) continue;
      checked++;
      for (const type of types) {
        if (!DESTINATION_TYPES.includes(type)) {
          annotateFailure(`  ${row.file || row.name || set.relPath}: invalid type "${type}".`);
          invalid++;
        }
      }
    }
  }

  console.log(`Types: ${checked} checked, ${invalid} invalid`);
  return invalid;
}

// Every `links[].type` across the hydrated rows is in the vocabulary. One of the
// checks in main()'s validate block, and the one that would have caught the
// label-rename breakage: since `type` is now the key every renderer selects by, a
// typo there silently drops the link out of its column instead of failing.
//
// VOCABULARY ONLY, never presence — an untyped link is a legitimate link.
function validateLinks(hydratedSets) {
  let checked = 0;
  let invalid = 0;

  for (const set of hydratedSets) {
    for (const row of set.hydrated) {
      for (const link of row.links || []) {
        if (!link || link.type === undefined) continue;
        checked++;
        if (!LINK_TYPES.includes(link.type)) {
          annotateFailure(`  ${row.file || row.name || set.relPath}: invalid link type "${link.type}" on "${link.label}".`);
          invalid++;
        }
      }
    }
  }

  console.log(`Links: ${checked} checked, ${invalid} invalid`);
  return invalid;
}

// Every manifest-listed dataset resolved into publishable rows. One of the checks
// in main()'s validate block; reports what loadHydratedListSet collected — a file
// that would not parse, or a `{file}` pointer with no page data behind it.
function validateLists(hydratedSets) {
  let invalid = 0;
  for (const set of hydratedSets) {
    if (!set.problems.length) continue;
    invalid++;
    for (const problem of set.problems) {
      annotateFailure(`  ${problem}`);
    }
  }
  console.log(`Lists: ${hydratedSets.length} checked, ${invalid} invalid`);
  return invalid;
}

async function syncFiles(fileBirdFolderCache, excludedSet) {
  console.log("\n=== Syncing files (Media) ===");
  let successCount = 0;
  let failCount = 0;

  if (!fs.existsSync(MEDIA_ROOT)) {
    console.warn(`[files] media root not found at ${MEDIA_ROOT} — nothing to sync.`);
    return { successCount, failCount };
  }

  const allEntries = fs.readdirSync(MEDIA_ROOT, { recursive: true });
  const filenames = allEntries.filter((f) => f.endsWith(".json") || f.endsWith(".jst") || f.endsWith(".cst") || f.endsWith(".pdf"));

  // Copy every file verbatim (CHANGED-gated in incremental mode). The hydrated
  // dataset lists are skipped here — they're handled by syncHydratedLists(),
  // which transforms them and runs unconditionally.
  for (const relSubPath of filenames) {
    const normalized = relSubPath.split(path.sep).join("/");

    if (excludedSet.has(normalized)) {
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

// Publish the hydrated dataset files, then the manifest itself with each entry's
// counts attached. UNCONDITIONAL every run (bypasses the CHANGED gate), so a
// changed page is always reflected in the hydrated output even when the list file
// itself didn't change.
//
// PUSH ONLY — it is handed what loadHydratedListSet built and the validate block
// already cleared, so there is nothing here to read, merge or decide. Serialize
// and upload.
async function syncHydratedLists(fileBirdFolderCache, hydratedSets) {
  console.log("\n=== Syncing hydrated lists ===");
  let successCount = 0;
  let failCount = 0;

  // The manifest as it will be published: one entry per dataset that made it,
  // the authored fields plus the collected counts.
  const publishedDatasets = [];

  for (const set of hydratedSets) {
    const filename = path.basename(set.relPath);
    const fileBuffer = Buffer.from(JSON.stringify(set.hydrated, null, 2));
    const mediaId = await syncOneFileToWordPress(set.relPath, filename, fileBuffer, guessMimeFromExt(filename));

    if (mediaId) {
      successCount++;
      await syncOneFileToFileBird(fileBirdFolderCache, mediaId, set.relPath);
      publishedDatasets.push({ ...set.dataset, counts: set.counts });
    } else {
      failCount++;
    }
  }

  // The manifest describes what was just published, so it goes out only when
  // every dataset made it. Leaving the previous copy on WP beats advertising a
  // vocabulary for data that didn't publish.
  if (failCount === 0) {
    const manifestName = path.basename(MANIFEST_REL);
    const fileBuffer = Buffer.from(JSON.stringify(publishedDatasets, null, 2));
    const mediaId = await syncOneFileToWordPress(MANIFEST_REL, manifestName, fileBuffer, guessMimeFromExt(manifestName));

    if (mediaId) {
      successCount++;
      await syncOneFileToFileBird(fileBirdFolderCache, mediaId, MANIFEST_REL);
    } else {
      failCount++;
    }
  }

  return { successCount, failCount };
}

// Publish the entire logs/ tree to /wp-content/uploads/<filename> and file it
// in FileBird under a top-level "logs" folder (peer of "data" and "images").
// The WP upload path is flat (by basename), so logs/locations.json is fetchable
// at /wp-content/uploads/locations.json — that's what the googleMap renderer
// reads to resolve location.location_id. Walked generically so future log files
// (travel-log maps, etc.) sync without touching this code.
async function syncLogs(fileBirdFolderCache) {
  console.log("\n=== Syncing logs ===");
  let successCount = 0;
  let failCount = 0;

  if (!fs.existsSync(LOGS_ROOT)) {
    console.warn(`[logs] logs root not found at ${LOGS_ROOT} — nothing to sync.`);
    return { successCount, failCount };
  }

  const allEntries = fs.readdirSync(LOGS_ROOT, { recursive: true });

  for (const relSubPath of allEntries) {
    const filePath = path.join(LOGS_ROOT, relSubPath);
    if (!fs.statSync(filePath).isFile()) continue;

    const filename = path.basename(filePath);
    if (filename.startsWith(".")) continue; // skip .DS_Store and other dotfiles

    // Relative to REPO_ROOT so the FileBird folder path is "logs" (or "logs/<sub>").
    const relPath = path.posix.relative(REPO_ROOT, filePath);

    if (CHANGED && !CHANGED.files.has(relPath)) {
      continue;
    }

    const fileBuffer = fs.readFileSync(filePath);
    const mimeType = guessMimeFromExt(filename);

    const mediaId = await syncOneFileToWordPress(relPath, filename, fileBuffer, mimeType);

    if (mediaId) {
      successCount++;
      await syncOneFileToFileBird(fileBirdFolderCache, mediaId, relPath);
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

  // ---- LOAD: read everything, derive everything that will be published -------
  console.log("=== Loading data maps ===");
  const perPageDataMap = loadPerPageDataMap();
  const datasets = loadDatasetManifest();
  const excludedSet = buildExcludedSet(datasets);
  const hydratedListSet = loadHydratedListSet(datasets, perPageDataMap);
  const wpPageMap = await loadWpPageMap();
  const wpPostMap = await loadWpPostMap();
  const wpMediaMap = await loadWpMediaMap();
  const ghPageMap = buildGhPageMap();
  const ghPostMap = buildGhPostMap();
  const glPageMap = generatePageMap(ghPageMap, perPageDataMap);

  // ---- VALIDATE: every check runs, THEN the block decides --------------------
  //
  // Running them all means one run reports everything that is wrong, instead of
  // making Pierre fix one thing to discover the next. Each check streams its own
  // failures as it finds them and closes with a tally line, so nothing has to be
  // accumulated here.
  //
  // A failure stops the run before ANY push. Failing halfway through, with the
  // site half updated, was the old behavior and it was a bug: an invalid leg was
  // reported and then the whole site went out anyway.
  console.log("\n=== Validating ===");
  let invalidCount = 0;
  invalidCount += validateLegs(perPageDataMap);
  invalidCount += validateTypes(hydratedListSet);
  invalidCount += validateLinks(hydratedListSet);
  invalidCount += validateLists(hydratedListSet);

  if (invalidCount > 0) {
    console.log("FAILED — nothing pushed.");
    process.exit(1);
  }

  // ---- PUSH: tell WordPress about what is already decided --------------------
  //
  // Each step announces its own section header and returns { successCount,
  // failCount }; the name is attached here because it is a label in this report,
  // not something a sync step should know about itself. Adding a step means adding
  // ONE line — the summary and the exit code follow from it. Validation is not in
  // this list: a run that gets here has already passed, and the summary is about
  // what was pushed.
  const results = [];
  results.push({ name: "Pages", ...await syncPages(pageFolderCache, ghPageMap, wpPageMap, perPageDataMap, wpMediaMap) });
  results.push({ name: "Posts", ...await syncPosts(pageFolderCache, ghPostMap, wpPostMap, perPageDataMap, wpMediaMap) });
  results.push({ name: "Files", ...await syncFiles(fileBirdFolderCache, excludedSet) });
  results.push({ name: "Lists", ...await syncHydratedLists(fileBirdFolderCache, hydratedListSet) });
  results.push({ name: "Logs", ...await syncLogs(fileBirdFolderCache) });
  results.push({ name: "PageMap", ...await syncPageMap(glPageMap, fileBirdFolderCache) });

  console.log("\n=== Summary ===");
  for (const result of results) {
    console.log(`${(result.name + ":").padEnd(10)}${String(result.successCount).padStart(3)} ok, ${String(result.failCount).padStart(3)} failed`);
  }

  const totalFails = results.reduce((sum, result) => sum + result.failCount, 0);
  if (totalFails > 0) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
