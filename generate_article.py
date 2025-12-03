import os
import random
from datetime import datetime
import requests
import textwrap
import pathlib

KEYWORDS = [
    "best ai tools for students in 2025",
    "ai tools for youtube content creators",
    "best ai writing tools for bloggers",
    "best task management apps for remote workers",
    "ai tools for video editing beginners",
    "ai tools for editing youtube thumbnails",
    "best note taking apps for university students",
    "best password managers for beginners",
    "best vpn for digital nomads 2025",
    "lightweight laptops for remote work under 1000",
    "best standing desks for home office",
    "ergonomic office chairs for programmers",
    "best microphones for podcasting on a budget",
    "affordable cameras for youtube beginners",
    "ai tools for social media scheduling",
    "best chrome extensions for productivity",
    "ai tools to summarize long articles",
    "best time tracking apps for freelancers",
    "ai tools for learning languages faster",
    "ai tools to improve focus and block distractions",
    "best budget noise cancelling headphones for work",
    "ai tools for creating online courses",
    "ai tools for designing logos and branding",
    "best cloud storage options for students",
    "ai tools to automate repetitive computer tasks"
]


def pick_topic() -> str:
    return random.choice(KEYWORDS)

def call_llm(prompt: str) -> str:
    api_key = os.environ.get("LLM_API_KEY")
    base_url = os.environ.get("LLM_API_BASE", "").rstrip("/")
    model = os.environ.get("LLM_MODEL")

    if not api_key or not base_url or not model:
        raise RuntimeError("LLM_API_KEY, LLM_API_BASE või LLM_MODEL pole seadistatud.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert SEO content writer. "
                    "Write in clear English, with headings and bullet points. "
                    "Target long-tail search queries and be genuinely helpful."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 1800,
        "temperature": 0.8,
    }

    resp = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=data,
        timeout=60
    )
    resp.raise_for_status()
    j = resp.json()
    return j["choices"][0]["message"]["content"]

def slugify(title: str) -> str:
    slug = (
        title.lower()
        .replace(" ", "-")
        .replace("?", "")
        .replace(",", "")
        .replace(":", "")
        .replace("'", "")
        .replace("\"", "")
        .replace("/", "-")
        .replace("*", "")
    )
    return slug


def make_front_matter(title: str, slug: str, date_str: str) -> str:
    fm = f"""---
title: "{title}"
date: "{date_str}"
slug: "{slug}"
---

"""
    return fm

def main():
    topic = pick_topic()

    prompt = textwrap.dedent(
        f"""
        Write a detailed 1500-word SEO article about: "{topic}".

        Requirements:
        - Start with a strong H1 title.
        - Use multiple H2 and H3 headings.
        - Use bullet lists where helpful.
        - Explain concepts clearly for beginners.
        - Include a section called "Recommended tools and products"
          where you list 3-5 tools or products in neutral tone.
        - Do NOT include any prices.
        - End with a short conclusion and a call to action
          (e.g. bookmark, share, or read another article).
        """
    ).strip()

    content = call_llm(prompt)

    lines = content.strip().splitlines()
    if lines and lines[0].startswith("#"):
        title = lines[0].lstrip("#").strip()
        body = "\n".join(lines[1:]).strip()
    else:
        title = topic.capitalize()
        body = content

    now = datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")
    slug = slugify(title)

    fm = make_front_matter(title, slug, date_str)
    full_md = fm + "\n" + body + "\n"

    posts_dir = pathlib.Path("content") / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)

    filename = posts_dir / f"{slug}.md"
    if filename.exists():
        filename = posts_dir / f"{slug}-{int(now.timestamp())}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_md)

    print(f"Generated article: {filename}")

if __name__ == "__main__":
    main()
