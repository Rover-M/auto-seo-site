import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

import markdown


BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content" / "posts"
DOCS_DIR = BASE_DIR / "docs"
POSTS_OUTPUT_DIR = DOCS_DIR / "posts"

# GitHub Pages repo path ja täielik URL
BASE_PATH = "/auto-seo-site"
BASE_URL = f"https://rover-m.github.io{BASE_PATH}"

SITE_TITLE = "Fuel Cards & Road Tolls Guide"
SITE_TAGLINE = "Practical guides for Baltic and European trucking companies to save on fuel and road tolls."


# --------------- UTILITIES ---------------

def ensure_dirs():
    DOCS_DIR.mkdir(exist_ok=True)
    POSTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_front_matter_and_body(text: str) -> (Dict[str, Any], str):
    """
    Expect format:

    ---
    title: "Some title"
    date: "2025-12-03 10:30:00"
    slug: "some-title"
    ---
    Body markdown...
    """
    fm_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    m = re.match(fm_pattern, text, re.DOTALL)
    if not m:
        return {}, text

    fm_text, body = m.groups()
    fm: Dict[str, Any] = {}
    for line in fm_text.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        fm[key] = value
    return fm, body


def load_posts() -> List[Dict[str, Any]]:
    posts: List[Dict[str, Any]] = []

    for path in sorted(CONTENT_DIR.glob("*.md")):
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()

        fm, body_md = parse_front_matter_and_body(raw)

        title = fm.get("title", path.stem)
        slug = fm.get("slug", path.stem)
        date_str = fm.get("date", "")
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            date = datetime.min

        body_html = markdown.markdown(body_md, extensions=["extra", "tables"])
        excerpt_text = make_excerpt_from_html(body_html, max_chars=220)

        posts.append(
            {
                "title": title,
                "slug": slug,
                "date": date,
                "date_str": date_str,
                "body_md": body_md,
                "body_html": body_html,
                "excerpt": excerpt_text,
            }
        )

    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def strip_html_tags(html: str) -> str:
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def make_excerpt_from_html(html: str, max_chars: int = 200) -> str:
    text = strip_html_tags(html)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rsplit(" ", 1)[0] + "..."


def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# --------------- TEMPLATES ---------------

BASE_CSS = """
body {
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    margin: 0;
    padding: 0;
    background: #0b1020;
    color: #f5f5f5;
}

a {
    color: #4fd1c5;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

header {
    background: #050816;
    padding: 1.5rem 1.5rem 1rem 1.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}

header h1 {
    margin: 0;
    font-size: 1.8rem;
}

header p {
    margin: 0.3rem 0 0;
    color: #a0aec0;
    max-width: 700px;
}

.layout {
    display: flex;
    flex-direction: row;
    align-items: flex-start;
    gap: 2rem;
    padding: 1.5rem;
}

main {
    flex: 1;
    max-width: 840px;
    background: rgba(15,23,42,0.9);
    border-radius: 14px;
    padding: 1.5rem 1.7rem;
    box-shadow: 0 16px 40px rgba(0,0,0,0.45);
}

aside {
    width: 280px;
    flex-shrink: 0;
    background: rgba(15,23,42,0.9);
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    box-shadow: 0 16px 40px rgba(0,0,0,0.45);
    position: sticky;
    top: 1.5rem;
    max-height: calc(100vh - 3rem);
    overflow-y: auto;
}

footer {
    padding: 1.5rem;
    text-align: center;
    font-size: 0.85rem;
    color: #a0aec0;
}

.post-meta {
    font-size: 0.9rem;
    color: #a0aec0;
    margin-bottom: 0.7rem;
}

.post-list-item {
    padding: 1rem 1rem 0.8rem 1rem;
    margin-bottom: 0.7rem;
    border-radius: 10px;
    background: rgba(15,23,42,0.85);
    border: 1px solid rgba(148,163,184,0.25);
}

.post-list-item h2 {
    margin: 0 0 0.3rem 0;
    font-size: 1.1rem;
}

.post-list-item p {
    margin: 0.3rem 0 0.2rem 0;
    color: #cbd5e1;
    font-size: 0.95rem;
}

.chip {
    display: inline-block;
    font-size: 0.75rem;
    padding: 0.15rem 0.5rem;
    border-radius: 999px;
    border: 1px solid rgba(148,163,184,0.6);
    color: #e2e8f0;
    margin-top: 0.2rem;
}

.post-content h1, .post-content h2, .post-content h3 {
    color: #e2e8f0;
}

.post-content h1 {
    margin-top: 0;
    margin-bottom: 0.6rem;
}

.post-content h2, .post-content h3 {
    margin-top: 1.2rem;
}

.post-content p {
    line-height: 1.6;
    color: #cbd5e1;
}

.post-content ul, .post-content ol {
    padding-left: 1.2rem;
}

.badge {
    display: inline-block;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 0.12rem 0.5rem;
    border-radius: 999px;
    background: rgba(79,209,197,0.16);
    color: #4fd1c5;
    margin-bottom: 0.4rem;
}

.hero-intro {
    margin-bottom: 1.4rem;
}

.hero-intro h2 {
    margin: 0 0 0.4rem 0;
    font-size: 1.4rem;
}

.hero-intro p {
    margin: 0;
    color: #cbd5e1;
}

.related-list {
    margin-top: 2.2rem;
    border-top: 1px solid rgba(148,163,184,0.35);
    padding-top: 1.2rem;
}

.related-list h3 {
    margin-top: 0;
    margin-bottom: 0.6rem;
}

.related-list ul {
    padding-left: 1.1rem;
}

.ad-block {
    border-radius: 12px;
    padding: 0.85rem 0.95rem;
    margin-bottom: 0.8rem;
    background: linear-gradient(135deg, rgba(56,189,248,0.18), rgba(79,209,197,0.08));
    border: 1px solid rgba(148,163,184,0.5);
    font-size: 0.9rem;
}

.ad-block h3 {
    margin: 0 0 0.3rem 0;
    font-size: 0.95rem;
}

.ad-block p {
    margin: 0.2rem 0;
}

.small-note {
    font-size: 0.8rem;
    color: #a0aec0;
    margin-top: 0.4rem;
}

.nav-links {
    margin-top: 0.7rem;
    font-size: 0.9rem;
}

.nav-links a {
    margin-right: 0.6rem;
    color: #e2e8f0;
}
"""


SIDEBAR_HTML = """
<div class="ad-block">
  <h3>Save on fuel across Europe</h3>
  <p>Compare fuel card offers and get better diesel prices for your fleet.</p>
  <p><a href="https://your-fuel-card-partner-link.com" target="_blank" rel="nofollow noopener">Check fuel card partners →</a></p>
  <p class="small-note">Affiliate link – we may earn a commission at no extra cost to you.</p>
</div>

<div class="ad-block">
  <h3>Automate toll payments</h3>
  <p>Use a single toll device for multiple EU countries and reduce admin overhead.</p>
  <p><a href="https://your-toll-partner-link.com" target="_blank" rel="nofollow noopener">View toll management options →</a></p>
</div>

<div class="ad-block">
  <h3>Need help with fines?</h3>
  <p>Some service providers can handle Polish and German toll fines for you.</p>
  <p><em>(Place your partner or lead form link here later.)</em></p>
</div>
"""


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{page_title}</title>
  <meta name="description" content="{meta_description}" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="canonical" href="{canonical_url}" />
  <meta property="og:title" content="{page_title}" />
  <meta property="og:description" content="{meta_description}" />
  <meta property="og:type" content="{og_type}" />
  <meta property="og:url" content="{canonical_url}" />
  <style>
  {base_css}
  </style>
</head>
<body>
  <header>
    <h1>{site_title}</h1>
    <p>{site_tagline}</p>
    <div class="nav-links">
      <a href="{base_path}/index.html">Home</a>
      <a href="{base_path}/posts.html">All guides</a>
    </div>
  </header>
  <div class="layout">
    <main>
      {main_html}
    </main>
    <aside>
      {sidebar_html}
    </aside>
  </div>
  <footer>
    &copy; {year} Fuel Cards &amp; Road Tolls Guide. Informational content only – not legal or financial advice.
  </footer>
</body>
</html>
"""


# --------------- PAGE GENERATION ---------------

def build_post_pages(posts: List[Dict[str, Any]]):
    year_now = datetime.utcnow().year

    for post in posts:
        title = post["title"]
        slug = post["slug"]
        date_str = post["date_str"]
        body_html = post["body_html"]
        excerpt = post["excerpt"]

        related_items = []
        for other in posts:
            if other["slug"] == slug:
                continue
            related_items.append(other)
            if len(related_items) >= 4:
                break

        related_html_parts = [
            '<div class="related-list">',
            "<h3>More practical guides</h3>",
            "<ul>",
        ]
        for other in related_items:
            other_title = html_escape(other["title"])
            other_slug = other["slug"]
            related_html_parts.append(
                f'<li><a href="{other_slug}.html">{other_title}</a></li>'
            )
        related_html_parts.append("</ul></div>")
        related_html = "\n".join(related_html_parts)

        main_html = f"""
<div class="post-content">
  <div class="badge">Trucking · Fuel · Tolls</div>
  <h1>{html_escape(title)}</h1>
  <div class="post-meta">Published: {html_escape(date_str)}</div>
  {body_html}
  {related_html}
</div>
        """.strip()

        meta_description = html_escape(excerpt or SITE_TAGLINE)
        page_title = f"{title} | {SITE_TITLE}"
        canonical_url = f"{BASE_URL}/posts/{slug}.html"

        html = PAGE_TEMPLATE.format(
            page_title=page_title,
            meta_description=meta_description,
            base_css=BASE_CSS,
            site_title=SITE_TITLE,
            site_tagline=SITE_TAGLINE,
            main_html=main_html,
            sidebar_html=SIDEBAR_HTML,
            year=year_now,
            base_path=BASE_PATH,
            canonical_url=canonical_url,
            og_type="article",
        )

        out_path = POSTS_OUTPUT_DIR / f"{slug}.html"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"Wrote post page: {out_path}")


def build_index_page(posts: List[Dict[str, Any]]):
    year_now = datetime.utcnow().year

    latest_posts = posts[:5]

    list_html_parts = []
    for p in latest_posts:
        title = html_escape(p["title"])
        slug = p["slug"]
        date_str = html_escape(p["date_str"])
        excerpt = html_escape(p["excerpt"])
        list_html_parts.append(
            f"""
<div class="post-list-item">
  <div class="chip">Guide</div>
  <h2><a href="posts/{slug}.html">{title}</a></h2>
  <div class="post-meta">{date_str}</div>
  <p>{excerpt}</p>
</div>
"""
        )

    posts_block = "\n".join(list_html_parts) or "<p>No posts yet – new guides will appear here over time.</p>"

    main_html = f"""
<div class="hero-intro">
  <div class="badge">Knowledge base</div>
  <h2>Save on diesel, tolls and admin work.</h2>
  <p>We publish practical guides for Baltic and European trucking companies. Topics include fuel cards, road tolls, compliance and fleet optimisation.</p>
</div>

<h2>Latest guides</h2>
{posts_block}

<p style="margin-top: 1.4rem;"><a href="posts.html">Browse all guides →</a></p>
""".strip()

    meta_description = html_escape(SITE_TAGLINE)
    canonical_url = f"{BASE_URL}/index.html"

    html = PAGE_TEMPLATE.format(
        page_title=SITE_TITLE,
        meta_description=meta_description,
        base_css=BASE_CSS,
        site_title=SITE_TITLE,
        site_tagline=SITE_TAGLINE,
        main_html=main_html,
        sidebar_html=SIDEBAR_HTML,
        year=year_now,
        base_path=BASE_PATH,
        canonical_url=canonical_url,
        og_type="website",
    )

    out_path = DOCS_DIR / "index.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Wrote index page: {out_path}")


def build_posts_list_page(posts: List[Dict[str, Any]]):
    year_now = datetime.utcnow().year

    list_html_parts = []
    for p in posts:
        title = html_escape(p["title"])
        slug = p["slug"]
        date_str = html_escape(p["date_str"])
        excerpt = html_escape(p["excerpt"])
        list_html_parts.append(
            f"""
<div class="post-list-item">
  <div class="chip">Guide</div>
  <h2><a href="posts/{slug}.html">{title}</a></h2>
  <div class="post-meta">{date_str}</div>
  <p>{excerpt}</p>
</div>
"""
        )

    posts_block = "\n".join(list_html_parts) or "<p>No posts yet – new guides will appear here over time.</p>"

    main_html = f"""
<h2>All trucking, fuel & toll guides</h2>
<p>Browse every article available on the site. New guides are added over time.</p>

{posts_block}
""".strip()

    meta_description = "All guides about fuel cards, road tolls and trucking cost optimisation in Europe."
    canonical_url = f"{BASE_URL}/posts.html"

    html = PAGE_TEMPLATE.format(
        page_title=f"All guides | {SITE_TITLE}",
        meta_description=html_escape(meta_description),
        base_css=BASE_CSS,
        site_title=SITE_TITLE,
        site_tagline=SITE_TAGLINE,
        main_html=main_html,
        sidebar_html=SIDEBAR_HTML,
        year=year_now,
        base_path=BASE_PATH,
        canonical_url=canonical_url,
        og_type="website",
    )

    out_path = DOCS_DIR / "posts.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Wrote posts list page: {out_path}")


# --------------- SITEMAP & ROBOTS ---------------

def build_sitemap(posts: List[Dict[str, Any]]):
    """Genereerib docs/sitemap.xml kõigi oluliste URL-idega."""
    urls = []

    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Avaleht ja kõigi postide list
    urls.append({"loc": f"{BASE_URL}/index.html", "lastmod": today})
    urls.append({"loc": f"{BASE_URL}/posts.html", "lastmod": today})

    for p in posts:
        slug = p["slug"]
        loc = f"{BASE_URL}/posts/{slug}.html"
        if p["date"] and p["date"] != datetime.min:
            lastmod = p["date"].strftime("%Y-%m-%d")
        else:
            lastmod = today
        urls.append({"loc": loc, "lastmod": lastmod})

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{u['loc']}</loc>")
        lines.append(f"    <lastmod>{u['lastmod']}</lastmod>")
        lines.append("  </url>")
    lines.append("</urlset>")

    sitemap_path = DOCS_DIR / "sitemap.xml"
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote sitemap: {sitemap_path}")


def build_robots():
    """Genereerib docs/robots.txt faili."""
    robots_text = f"""User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap.xml
"""
    robots_path = DOCS_DIR / "robots.txt"
    with open(robots_path, "w", encoding="utf-8") as f:
        f.write(robots_text)

    print(f"Wrote robots.txt: {robots_path}")


# --------------- MAIN ---------------

def main():
    ensure_dirs()
    posts = load_posts()
    build_post_pages(posts)
    build_index_page(posts)
    build_posts_list_page(posts)
    build_sitemap(posts)
    build_robots()


if __name__ == "__main__":
    main()
