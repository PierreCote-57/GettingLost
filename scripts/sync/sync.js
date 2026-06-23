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
 *      Uses config/page-map.json to know which WordPress page ID
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

const REPO_ROOT = path.resolve(__dirname, "..", "..");

const WP_SITE_URL = requireEnv("WP_SITE_URL").replace(/\/$/, "");
const WP_USER = requireEnv("WP_USER");
const WP_APP_PASSWORD = requireEnv("WP_APP_PASSWORD");

const AUTH_HEADER =
  "Basic " + Buffer.from(`${WP_USER}:${WP_APP_PASSWORD}`).toString("base64");

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

// ---------------------------------------------------------------------
// PAGES sync
// ---------------------------------------------------------------------

async function syncPages() {
  const pageMapPath = path.join(REPO_ROOT, "config", "page-map.json");
  const pageMap = JSON.parse(fs.readFileSync(pageMapPath, "utf8"));

  const pageDirs = {
    lakes: path.join(REPO_ROOT, "pages", "lakes"),
    parks: path.join(REPO_ROOT, "pages", "parks"),
    campgrounds: path.join(REPO_ROOT, "pages", "campgrounds"),
    templates: path.join(REPO_ROOT, "pages", "templates"),
    site: path.join(REPO_ROOT, "pages", "site"),
  };

  let successCount = 0;
  let failCount = 0;

  for (const [category, slugToId] of Object.entries(pageMap)) {
    const dir = pageDirs[category];
    if (!dir) {
      console.warn(`No page directory configured for category "${category}" — skipping.`);
      continue;
    }

    for (const [slug, pageId] of Object.entries(slugToId)) {
      const filePath = path.join(dir, `${slug}.html`);
      if (!fs.existsSync(filePath)) {
        console.warn(`[pages] ${category}/${slug}: no file at ${filePath} — skipping.`);
        continue;
      }

      const content = fs.readFileSync(filePath, "utf8");

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

const FILE_SOURCE_DIRS = [
  { dir: path.join(REPO_ROOT, "scripts"), mime: guessMimeFromExt },
  { dir: path.join(REPO_ROOT, "data", "lakes"), mime: () => "application/json" },
  { dir: path.join(REPO_ROOT, "data", "parks"), mime: () => "application/json" },
  { dir: path.join(REPO_ROOT, "data", "campgrounds"), mime: () => "application/json" },
  { dir: path.join(REPO_ROOT, "data", "site"), mime: () => "application/json" },
  { dir: path.join(REPO_ROOT, "gallery-data"), mime: () => "application/json" },
];

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

async function syncFiles() {
  let successCount = 0;
  let failCount = 0;

  for (const { dir, mime } of FILE_SOURCE_DIRS) {
    if (!fs.existsSync(dir)) continue;

    const filenames = fs
      .readdirSync(dir)
      .filter((f) => f.endsWith(".json") || f.endsWith(".jst"));

    for (const filename of filenames) {
      const filePath = path.join(dir, filename);
      const fileBuffer = fs.readFileSync(filePath);
      const mimeType = mime(filename);

      try {
        const existingId = await findExistingMediaIdByFilename(filename);
        if (existingId) {
          await deleteMedia(existingId);
        }
        await uploadMedia(filename, fileBuffer, mimeType);
        console.log(`[files] OK ${filename}${existingId ? " (overwritten)" : " (new)"}`);
        successCount++;
      } catch (err) {
        console.error(`[files] FAILED ${filename}:`, err.message);
        failCount++;
      }
    }
  }

  return { successCount, failCount };
}

// ---------------------------------------------------------------------
// Gallery JSON sync (Destinations/Lakes/Parks/Campgrounds in
// gallery-data/) is already covered by syncFiles() above since
// gallery-data/ is in FILE_SOURCE_DIRS — no special-casing needed.
// ---------------------------------------------------------------------

// ---------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------

async function main() {
  console.log(`Syncing to ${WP_SITE_URL} ...\n`);

  console.log("=== Syncing files (JSON data + scripts) ===");
  const filesResult = await syncFiles();

  console.log("\n=== Syncing pages ===");
  const pagesResult = await syncPages();

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
