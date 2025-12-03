import os
import pathlib
from datetime import datetime
import markdown

CONTENT_DIR = pathlib.Path("content/posts")
DOCS_DIR = pathlib.Path("docs")
POSTS_OUTPUT_DIR = DOCS_DIR / "posts"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      max-width: 900px;
      margin: 40px auto;
      padding: 0 16px;
      line-height: 1.6;
    }}
    a {{
      color: #2563eb;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    h1, h2, h3 {{
      margin-top: 1.4em;
    }}
    .post-meta {{
      color: #6b7280;
      font-size: 0.9em;
      margin-bottom: 1em;
    }}
  </style>
</head>
<body>
  <header>
    <h1><a href="/auto-seo-site/">AI SEO Site</a></h1>
    <p>Automatically growing AI-generated content.</p>
    <p><a href="/auto-seo-site/posts.html">All posts</a></p>
  </header>
  <main>
  {content}
  </main>
</body>
</html>
"""

def parse_front_matter(md_text: str):
    lines = md_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, md_text

    fm_lines = []
    body_lines = []
    in_fm = True
    for line in lines[1:]:
        if in_fm:
            if line.strip() == "---":
                in_fm = False
            else:
                fm_lines.append(line)
        else:
            body_lines.append(line)

    meta = {}
    for l in fm_lines:
        if ":" in l:
            key, val = l.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            meta[key] = val
    body = "\n".join(body_lines)
    return meta, body

def build_site():
    DOCS_DIR.mkdir(exist_ok=True)
    POSTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    posts_info = []

    for md_path in sorted(CONTENT_DIR.glob("*.md")):
        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        meta, body_md = parse_front_matter(md_text)
        title = meta.get("title", md_path.stem)
        date_str = meta.get("date", "")
        slug = meta.get("slug", md_path.stem)

        html_body = markdown.markdown(body_md)

        post_html = f"""
<h1>{title}</h1>
<div class="post-meta">{date_str}</div>
{html_body}
"""
        out_path = POSTS_OUTPUT_DIR / f"{slug}.html"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(HTML_TEMPLATE.format(title=title, content=post_html))

        posts_info.append(
            {
                "title": title,
                "slug": slug,
                "date": date_str,
            }
        )

    posts_info.sort(key=lambda p: p["date"], reverse=True)
    items_html = ""
    for p in posts_info:
        items_html += (
            f'<li><a href="/auto-seo-site/posts/{p["slug"]}.html">'
            f'{p["title"]}</a> <span class="post-meta">({p["date"]})</span></li>\n'
        )

    posts_list_html = f"""
<h1>All posts</h1>
<ul>
{items_html}
</ul>
"""

    posts_page = HTML_TEMPLATE.format(title="All posts", content=posts_list_html)
    with open(DOCS_DIR / "posts.html", "w", encoding="utf-8") as f:
        f.write(posts_page)

    latest_html = ""
    for p in posts_info[:5]:
        latest_html += (
            f'<li><a href="/auto-seo-site/posts/{p["slug"]}.html">'
            f'{p["title"]}</a> <span class="post-meta">({p["date"]})</span></li>\n'
        )

    index_content = f"""
<h1>AI SEO Site</h1>
<p>This site automatically publishes AI-generated, SEO-optimized articles.</p>
<p><a href="/auto-seo-site/posts.html">View all posts</a></p>
<h2>Latest posts</h2>
<ul>
{latest_html}
</ul>
"""

    index_html = HTML_TEMPLATE.format(title="AI SEO Site", content=index_content)
    with open(DOCS_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

if __name__ == "__main__":
    build_site()
