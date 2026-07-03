#!/usr/bin/env node
/**
 * pull-posts.js
 *
 * Fetches WordPress posts that don't yet exist in the local repo and
 * writes them as posts/{slug}.html + media/data/posts/{slug}/{slug}.json.
 *
 * Once a post is in the repo, GitHub is master — this script never
 * overwrites existing local files.
 *
 * Usage:
 *   Run via GitHub Actions (pull-posts.yml workflow, manual trigger).
 *   Credentials come from GitHub Secrets.
 */

const fs = require("fs");
const path = require("path");

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const POSTS_ROOT = path.join(REPO_ROOT, "posts");
const POSTS_DATA_ROOT = path.join(REPO_ROOT, "media", "data", "posts");

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

function loadLocalSlugs() {
  const slugs = new Set();
  if (!fs.existsSync(POSTS_ROOT)) return slugs;

  const entries = fs.readdirSync(POSTS_ROOT);
  for (const entry of entries) {
    if (entry.endsWith(".html")) {
      slugs.add(path.basename(entry, ".html"));
    }
  }
  return slugs;
}

async function fetchAllWpPosts() {
  const posts = [];
  let page = 1;
  while (true) {
    const res = await wpFetch(`/posts?per_page=100&page=${page}&status=any&context=edit`);
    if (!res.ok) throw new Error(`post listing failed: HTTP ${res.status}`);
    const items = await res.json();
    posts.push(...items);
    const totalPages = parseInt(res.headers.get("X-WP-TotalPages") || "1", 10);
    if (page >= totalPages) break;
    page++;
  }
  return posts;
}

async function buildReverseMediaMap() {
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
        map.set(item.id, urlPath);
      } catch {
        map.set(item.id, item.source_url);
      }
    }
    const totalPages = parseInt(res.headers.get("X-WP-TotalPages") || "1", 10);
    if (page >= totalPages) break;
    page++;
  }
  return map;
}

function stripParagraphWrap(html) {
  if (!html) return "";
  return html.replace(/^<p>/, "").replace(/<\/p>\s*$/, "").trim();
}

async function main() {
  console.log(`Pulling posts from ${WP_SITE_URL} ...\n`);

  const localSlugs = loadLocalSlugs();
  console.log(`[local] ${localSlugs.size} post(s) already in repo.`);

  const wpPosts = await fetchAllWpPosts();
  console.log(`[wp] ${wpPosts.length} post(s) found in WordPress.\n`);

  const newPosts = wpPosts.filter((p) => !localSlugs.has(p.slug));
  if (newPosts.length === 0) {
    console.log("No new posts to pull — everything is already in the repo.");
    return;
  }

  console.log(`${newPosts.length} new post(s) to pull.\n`);

  const reverseMediaMap = await buildReverseMediaMap();

  fs.mkdirSync(POSTS_ROOT, { recursive: true });
  fs.mkdirSync(POSTS_DATA_ROOT, { recursive: true });

  let created = 0;
  for (const post of newPosts) {
    const slug = post.slug;
    const htmlPath = path.join(POSTS_ROOT, `${slug}.html`);
    const jsonDir = path.join(POSTS_DATA_ROOT, slug);
    const jsonPath = path.join(jsonDir, `${slug}.json`);

    const content = post.content.raw || "";
    const title = post.title.raw || post.title.rendered || slug;
    const excerpt = stripParagraphWrap(post.excerpt.raw || post.excerpt.rendered || "");
    let featuredImage = null;
    if (post.featured_media) {
      const resolved = reverseMediaMap.get(post.featured_media);
      if (resolved) {
        featuredImage = path.basename(resolved);
      } else {
        console.warn(
          `[pull] ${slug}: featured_media ${post.featured_media} not found in media library — leaving featuredImage null.`
        );
      }
    }
    const date = post.date || "";
    const published = post.status === "publish";

    const jsonData = {
      title,
      excerpt,
      featuredImage,
      date,
      published,
      categories: [],
      tags: [],
    };

    fs.writeFileSync(htmlPath, content, "utf8");
    fs.mkdirSync(jsonDir, { recursive: true });
    fs.writeFileSync(jsonPath, JSON.stringify(jsonData, null, 2) + "\n", "utf8");

    console.log(`[pull] ${slug} — ${title}`);
    created++;
  }

  console.log(`\nDone. ${created} post(s) pulled.`);
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
