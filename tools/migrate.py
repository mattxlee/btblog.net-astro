#!/usr/bin/env python3
"""
Migrate a WordPress WXR export to Astro Markdown blog posts.

Reads serenity.WordPress.*.xml, converts each post to a Markdown file in
src/content/blog/ with frontmatter (title, pubDate, draft, categories, tags).
Content (Gutenberg-block HTML) is converted to pure Markdown via markdownify.
MathML blocks are extracted as LaTeX ($$...$$). Image URLs are rewritten to
local /uploads/... paths.
"""
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from urllib.parse import unquote, quote

from markdownify import markdownify as html_to_md

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XML_PATH = None
for fname in os.listdir(BASE):
    if fname.startswith("serenity.WordPress") and fname.endswith(".xml"):
        XML_PATH = os.path.join(BASE, fname)
        break
if not XML_PATH:
    backup_dir = os.path.join(BASE, "wordpress-backup")
    for fname in os.listdir(backup_dir):
        if fname.startswith("serenity.WordPress") and fname.endswith(".xml"):
            XML_PATH = os.path.join(backup_dir, fname)
            break
if not XML_PATH:
    sys.exit("No WordPress WXR export found in project root or wordpress-backup/.")

OUT_DIR = os.path.join(BASE, "src", "content", "blog")
os.makedirs(OUT_DIR, exist_ok=True)

NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wp": "http://wordpress.org/export/1.2/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
}

# ---------- helpers ----------

def clean_slug(s):
    """Decode a WP URL-encoded post_name into a filesystem-safe slug."""
    s = unquote(s or "")
    s = s.strip()
    if not s:
        return s
    # transliterate-ish: keep CJK + create ASCII slug via ascii folding for latin
    slug = ""
    for ch in s:
        if ch.isalnum():
            slug += ch
        elif ch in "-_.":
            slug += "-"
    slug = slug.lower()
    # keep CJK (they are alnum under unicode)
    slug = re.sub(r"-+", "-", slug).strip("-") or "untitled"
    return slug


def slug_from_title(title):
    """Generate a slug from a title when WP has none."""
    s = title.strip()
    s = re.sub(r"[《》「」『』“”’()（）?!？!，,。.·、：: ]", "-", s)
    s = clean_slug(s) or "untitled"
    return s


def extract_math_as_latex(html):
    """Replace each <math>...</math> with a display LaTeX block read from its
    <annotation encoding="application/x-tex"> (fallback: data-latex attr)."""
    def repl(m):
        block = m.group(0)
        # try annotation with x-tex
        ann = re.search(
            r'<annotation[^>]*encoding="application/x-tex"[^>]*>(.*?)</annotation>',
            block, re.S)
        tex = None
        if ann:
            tex = ann.group(1)
        else:
            dm = re.search(r'data-latex="([^"]*)"', block)
            if dm:
                tex = dm.group(1)
        if tex is None:
            return ""
        tex = tex.strip()
        return "\n\n$$\n" + tex + "\n$$\n\n"
    return re.sub(r'<math.*?</math>', repl, html, flags=re.S)

def rewrite_images(html):
    """Rewrite WP upload image URLs to local /uploads/ paths."""
    # Absolute URLs with wp-content/uploads prefix
    html = re.sub(
        r"https?://m\.btblog\.net/wp-content/uploads/",
        "/uploads/",
        html,
    )
    return html


def unwrap_formula_code_blocks(html):
    """WordPress sometimes wraps a MathML formula inside a <pre><code> block.
    After math extraction those become <pre><code>$$...$$</code></pre>. Unwrap
    such formula-only code blocks so they render as display math, not code."""
    pattern = re.compile(
        r"<pre[^>]*><code[^>]*>\s*(\$\$.*?\$\$)\s*</code></pre>",
        flags=re.S,
    )
    return pattern.sub(lambda m: f"\n\n{m.group(1)}\n\n", html)


def convert_content(html):
    """Full content pipeline: math -> images -> markdown -> cleanup."""
    html = extract_math_as_latex(html)
    html = unwrap_formula_code_blocks(html)
    html = rewrite_images(html)
    md = html_to_md(
        html,
        heading_style="ATX",
        bullets="-",
        strip=["script", "style"],
    )
    # collapse 3+ blank lines
    md = re.sub(r"\n{3,}", "\n\n", md)
    # tidy leftover Gutenberg comment wrappers
    md = re.sub(r"<!--\s*/?wp:.*?-->", "", md, flags=re.S)
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    return md + "\n"


def parse_date(s):
    """2026-04-21 19:46:14 -> 2026-04-21 19:46:14 (preserve date only for pubDate line)."""
    if not s:
        return None
    return s.strip()


def parse_author(it):
    a = it.find("dc:creator", NS)
    return a.text.strip() if a is not None and a.text else "matthew"


def list_section(item, tag):
    """Collect text of <category domain='...'> entries parsed as taxonomy."""
    out = []
    for c in item.iter("category"):
        dom = c.get("domain")
        if dom == tag and c.text:
            out.append(c.text.strip())
    return out


# ---------- parse ----------

tree = ET.parse(XML_PATH)
root = tree.getroot()
channel = root.find("channel")

posts = []
for item in channel.findall("item"):
    pt = item.find("wp:post_type", NS)
    ptype = pt.text if pt is not None else "post"
    if ptype != "post":
        continue  # skip attachments, global styles, navigation

    status_el = item.find("wp:status", NS)
    status = status_el.text if status_el is not None else "publish"
    title_el = item.find("title")
    title = title_el.text.strip() if title_el is not None and title_el.text else "Untitled"

    date_el = item.find("wp:post_date", NS)
    date = parse_date(date_el.text) if date_el is not None else None

    link_el = item.find("link")
    orig_url = link_el.text.strip() if link_el is not None and link_el.text else ""

    content_el = item.find("content:encoded", NS)
    raw = content_el.text or "" if content_el is not None else ""

    cats = list_section(item, "category")
    tags = list_section(item, "post_tag")

    posts.append({
        "title": title,
        "date": date,
        "draft": status == "draft",
        "orig_url": orig_url,
        "raw": raw,
        "categories": cats,
        "tags": tags,
    })

print(f"Parsed {len(posts)} posts from {XML_PATH}")

# ---------- write files ----------

written = []
for post in posts:
    md_body = convert_content(post["raw"])

    # determine filename slug
    slug = slug_from_title(post["title"])
    if post["date"]:
        dpart = post["date"].split(" ")[0]  # YYYY-MM-DD
    else:
        dpart = "no-date"
    fname = f"{dpart}-{slug}.md"
    # avoid collisions
    fpath = os.path.join(OUT_DIR, fname)
    n = 1
    while os.path.exists(fpath):
        fpath = os.path.join(OUT_DIR, f"{dpart}-{slug}-{n}.md")
        n += 1

    front = []
    front.append("---")
    front.append(f"title: {post['title']!r}".replace("\\'", "\\'"))
    front.append(f"pubDate: {post['date']}")
    front.append(f"draft: {'true' if post['draft'] else 'false'}")
    if post["categories"]:
        front.append("categories:")
        for c in post["categories"]:
            front.append(f"  - {c!r}".replace("\\'", "\\'"))
    if post["tags"]:
        front.append("tags:")
        for t in post["tags"]:
            front.append(f"  - {t!r}".replace("\\'", "\\'"))
    front.append(f"originalUrl: {post['orig_url']!r}".replace("\\'", "\\'"))
    front.append("---")
    front.append("")
    content = "\n".join(front) + md_body

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    written.append(fname)

print(f"Wrote {len(written)} Markdown files:")
for w in written:
    print("  -", w)

# ---------- copy images ----------
import shutil

def sync_images(src_root, dst_root):
    """Copy wordpress-backup/wp-content/uploads -> public/uploads recursively."""
    if not os.path.isdir(src_root):
        print(f"[images] source not found: {src_root}")
        return
    copied = 0
    for dirpath, _, files in os.walk(src_root):
        rel = os.path.relpath(dirpath, src_root)
        target_dir = os.path.join(dst_root, rel)
        os.makedirs(target_dir, exist_ok=True)
        for fn in files:
            s = os.path.join(dirpath, fn)
            d = os.path.join(target_dir, fn)
            if not os.path.exists(d) or os.path.getsize(s) != os.path.getsize(d):
                shutil.copy2(s, d)
                copied += 1
    print(f"[images] synced {copied} image(s) to {dst_root}")

WC_UPLOADS = os.path.join(BASE, "wordpress-backup", "wp-content", "uploads")
PUBLIC_UPLOADS = os.path.join(BASE, "public", "uploads")
sync_images(WC_UPLOADS, PUBLIC_UPLOADS)

