#!/usr/bin/env node
/**
 * slug-refactor.js
 *
 * One-shot migration to bring EXISTING WordPress slugs into the universal
 * "<base>_<ext>" format, IN PLACE. It changes the slug (post_name) only —
 * it NEVER touches the filename. The browser fetches data/media by filename
 * (source_url), so filenames must stay exactly as they are.
 *
 * Runs one content type at a time (media | pages | posts) so each can be
 * validated before the next. Dry run is the DEFAULT — nothing is written
 * unless --apply=true is passed.
 *
 * The model (deliberately un-fancy):
 *   - github filename is master.  desired slug = "<base>_<ext>" of that name
 *     (last "." -> "_", then WP-sanitised) — identical to sync.js's mediaSlug.
 *   - Walk every WP object of the chosen type and sort it into ONE bucket:
 *
 *       -N in slug or (media) filename ...... FLAGGED  (no action; you clean
 *                                                       up + re-sync from git)
 *       slug already == desired ............. OK       (skip)
 *       slug is a known base, needs fixing .. CHANGED  (dry run: PLANNED)
 *       object not represented in github .... FLAGGED  (orphan)
 *       write attempted, WP refused/bumped .. FAILED   (red)
 *
 *   Anything with a "-N" suffix is flagged, full stop — no winner-picking.
 *   Because github is master, a flagged duplicate is safe to delete: a later
 *   sync regenerates the correct object from the repo.
 *
 * Validation of a write:
 *   - media  : the response `slug` is truthful  -> compare it directly.
 *   - pages/ : the response `slug` LIES (echoes the request even when WP
 *     posts    stored a "-2") -> validate via the permalink (`link`).
 *
 * Auth/conventions mirror sync.js: WP Application Password (Basic Auth) via
 * WP_USER / WP_APP_PASSWORD, site via WP_SITE_URL.
 *
 * Usage:  node slug-refactor.js --type=media|pages|posts [--apply=true]
 */

const fs = require("fs");
const path = require("path");

// ---------------------------------------------------------------------
// Config (same conventions as sync.js)
// ---------------------------------------------------------------------

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const PAGES_ROOT = path.join(REPO_ROOT, "pages");
const POSTS_ROOT = path.join(REPO_ROOT, "posts");

const WP_SITE_URL = requireEnv("WP_SITE_URL").replace(/\/$/, "");
const WP_USER = requireEnv("WP_USER");
const WP_APP_PASSWORD = requireEnv("WP_APP_PASSWORD");
const AUTH_HEADER =
  "Basic " + Buffer.from(`${WP_USER}:${WP_APP_PASSWORD}`).toString("base64");

const TYPE = (getArg("--type") || "").toLowerCase(); // media | pages | posts
const APPLY = getArg("--apply") === "true"; // default: dry run

// ---------------------------------------------------------------------
// Small helpers (re-declared, not imported — sync.js runs main() on load)
// ---------------------------------------------------------------------

function requireEnv(name) {
  const value = process.env[name];
  if (!value) {
    console.error(`Missing required environment variable: ${name}`);
    process.exit(1);
  }
  return value;
}

function getArg(flag) {
  const a = process.argv.find((x) => x.startsWith(`${flag}=`));
  return a ? a.slice(flag.length + 1) : null;
}

function wpFetch(endpoint, options = {}) {
  const url = `${WP_SITE_URL}/wp-json/wp/v2${endpoint}`;
  return fetch(url, {
    ...options,
    headers: { Authorization: AUTH_HEADER, ...(options.headers || {}) },
  });
}

// Universal slug rule — byte-identical to sync.js sanitizeSlug + mediaSlug.
function sanitizeSlug(s) {
  return String(s)
    .toLowerCase()
    .replace(/[^a-z0-9 _-]/g, "")
    .trim()
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-");
}

function fileToSlug(filename) {
  const ext = path.extname(filename).replace(/^\./, "").toLowerCase();
  const base = path.basename(filename, path.extname(filename));
  return sanitizeSlug(`${base}_${ext}`);
}

// Authoritative slug for pages/posts — the create/update `slug` field can lie.
function slugFromLink(link) {
  try {
    const parts = new URL(link).pathname.split("/").filter(Boolean);
    return parts.length ? parts[parts.length - 1] : "";
  } catch (_) {
    return "";
  }
}

// WP's file-dedup suffix: a hyphen followed by digits at the very end.
// (Camera names like IMG_0706 use an UNDERSCORE, so they never match.)
const N_SUFFIX = /-\d+$/;

// ---------------------------------------------------------------------
// Logging (5 states + a tally). ANSI colours render in GitHub Actions.
// ---------------------------------------------------------------------

const C = {
  reset: "\x1b[0m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  dim: "\x1b[2m",
};

const tally = { planned: 0, ok: 0, changed: 0, flagged: 0, failed: 0 };

function line(label, color, ident, detail) {
  const id = ident ? ` ${C.dim}${ident}${C.reset}` : "";
  console.log(`${color}${label}${C.reset}${id}  ${detail}`);
}

function planned(ident, from, to) {
  tally.planned++;
  line("PLANNED", C.reset, ident, `${from} → ${to}`);
}
function ok(ident, slug) {
  tally.ok++;
  line("OK     ", C.green, ident, slug);
}
function changed(ident, from, to) {
  tally.changed++;
  line("CHANGED", C.reset, ident, `${from} → ${to}`);
}
function flagged(ident, slug, why) {
  tally.flagged++;
  line("FLAGGED", C.yellow, ident, `${slug}  (${why})`);
}
function failed(ident, from, to, why) {
  tally.failed++;
  line("FAILED ", C.red, ident, `${from} → ${to}  (${why})`);
}

// ---------------------------------------------------------------------
// WP enumeration + the single write primitive
// ---------------------------------------------------------------------

async function enumerate(type) {
  const items = [];
  let page = 1;
  const statusQ = type === "media" ? "" : "&status=any";
  while (true) {
    const res = await wpFetch(`/${type}?per_page=100&page=${page}${statusQ}`);
    if (!res.ok) throw new Error(`${type} listing failed: HTTP ${res.status}`);
    const batch = await res.json();
    items.push(...batch);
    const total = parseInt(res.headers.get("X-WP-TotalPages") || "1", 10);
    if (page >= total) break;
    page++;
  }
  return items;
}

// Set the slug of one object, or (dry run) just report the plan. Validates
// truthfully per type and reports CHANGED / FAILED / PLANNED.
async function setSlug(type, id, ident, from, to) {
  if (!APPLY) {
    planned(ident, from, to);
    return;
  }
  const res = await wpFetch(`/${type}/${id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ slug: to }),
  });
  if (!res.ok) {
    const text = (await res.text()).replace(/\s+/g, " ").slice(0, 200);
    failed(ident, from, to, `HTTP ${res.status} — ${text}`);
    return;
  }
  const updated = await res.json();
  // media slug is truthful; pages/posts must be read from the permalink.
  const actual = type === "media" ? updated.slug : slugFromLink(updated.link);
  if (actual !== to) {
    failed(ident, from, to, `WP stored "${actual}"`);
    return;
  }
  changed(ident, from, to);
}

// ---------------------------------------------------------------------
// Per-type processing
// ---------------------------------------------------------------------

// Media: desired slug comes from the object's OWN filename (source_url) —
// self-contained, no github lookup needed.
async function processMedia(items) {
  for (const obj of items) {
    const slug = obj.slug || "";
    const filename = obj.source_url
      ? path.basename(new URL(obj.source_url).pathname)
      : "";

    if (!filename) {
      flagged(`id ${obj.id}`, slug, "no source_url");
      continue;
    }

    const base = path.basename(filename, path.extname(filename));
    if (N_SUFFIX.test(base)) {
      flagged(filename, slug, "duplicate upload file (-N)");
      continue;
    }
    if (N_SUFFIX.test(slug)) {
      flagged(filename, slug, "-N slug");
      continue;
    }

    const desired = fileToSlug(filename);
    if (slug === desired) {
      ok(filename, slug);
      continue;
    }
    await setSlug("media", obj.id, filename, slug, desired);
  }
}

// Pages/posts: no WP filename exists, so desired comes from the github file
// (which also carries the true extension and tells us what's an orphan).
async function processPagesOrPosts(type, items) {
  const root = type === "pages" ? PAGES_ROOT : POSTS_ROOT;
  const desiredByBase = new Map(); // base -> desired slug
  const desiredSet = new Set(); // all desired slugs (already-migrated check)

  if (fs.existsSync(root)) {
    for (const entry of fs.readdirSync(root, { recursive: true })) {
      if (!entry.endsWith(".html")) continue;
      const filename = path.basename(entry);
      const base = path.basename(entry, ".html");
      const d = fileToSlug(filename);
      desiredByBase.set(base, d);
      desiredSet.add(d);
    }
  }

  for (const obj of items) {
    const slug = obj.slug || "";
    const title = (obj.title && obj.title.rendered) || "";
    const ident = title ? `«${title}»` : `id ${obj.id}`;

    if (N_SUFFIX.test(slug)) {
      flagged(ident, slug, "-N slug");
      continue;
    }
    if (desiredSet.has(slug)) {
      ok(ident, slug); // already migrated
      continue;
    }
    const desired = desiredByBase.get(slug);
    if (!desired) {
      flagged(ident, slug, "no matching github file (orphan)");
      continue;
    }
    await setSlug(type, obj.id, ident, slug, desired);
  }
}

// ---------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------

async function main() {
  if (!["media", "pages", "posts"].includes(TYPE)) {
    console.error(`--type must be one of media|pages|posts (got "${TYPE}")`);
    process.exit(1);
  }

  console.log(
    `slug-refactor: type=${TYPE}  mode=${
      APPLY ? "APPLY (writing to WP)" : "DRY RUN (no changes)"
    }\n`
  );

  const items = await enumerate(TYPE);
  console.log(`Enumerated ${items.length} ${TYPE} object(s) from WP.\n`);

  if (TYPE === "media") await processMedia(items);
  else await processPagesOrPosts(TYPE, items);

  console.log(`\n=== Summary (${TYPE}, ${APPLY ? "APPLY" : "DRY RUN"}) ===`);
  console.log(
    `${tally.planned} planned · ${tally.ok} OK · ${tally.changed} changed · ` +
      `${tally.flagged} flagged · ${tally.failed} failed`
  );

  // Fail the job on a real write error so it's visible in the Actions UI.
  if (tally.failed > 0) process.exit(1);
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
