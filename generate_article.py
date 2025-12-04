import os
import re
import textwrap
import random
from datetime import datetime, timezone
from typing import Tuple

import requests


# ------------------------------
#  LOGISTICS / FUEL COST NICHE
# ------------------------------
TOPIC_TEMPLATES = [
    # Fuel cards & fuel savings
    "best fuel cards for international trucking companies in {year}",
    "how Baltic transport companies can save on diesel costs in {year}",
    "fuel saving tips for small trucking fleets in {year}",
    "how to reduce fuel costs for long-haul trucks in {year}",

    # Road tolls (Poland, Germany, etc.)
    "complete guide to Polish road tolls for EU truckers in {year}",
    "road tolls in Germany explained for Baltic transport companies in {year}",
    "how to avoid common toll fines in Europe in {year}",
    "beginner's guide to European road toll systems for new trucking companies in {year}",

    # Fleet management & operations
    "how to optimize routes for Baltic trucking companies in {year}",
    "telematics and GPS tracking basics for small trucking fleets in {year}",
    "how to start a small trucking company in the Baltics in {year}",
    "best practices for managing driver fuel cards in {year}",

    # Compliance & fines
    "how to handle toll fines in Poland and avoid repeat penalties in {year}",
    "tachograph and driving time rules explained for new fleet managers in {year}",
    "checklist for staying compliant with EU road regulations in {year}",

    # Mixed topics
    "how to compare different fuel card providers in {year}",
    "how to choose the right fuel card for your trucking company in {year}",
    "ways to improve cash flow in a small transport company in {year} using fuel cards and payment terms",
]


def pick_topic() -> str:
    """Valib teema ja asendab {year} jooksva aastaga (timezone-aware)."""
    year = datetime.now(timezone.utc).year
    template = random.choice(TOPIC_TEMPLATES)
    return template.format(year=year)


# ------------------------------
#  FRONT MATTER
# ------------------------------

def slugify(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^a-z0-9]+", "-", title)
    return title.strip("-")


def make_front_matter(title: str, slug: str, date_str: str) -> str:
    fm = f"""---
title: "{title}"
date: "{date_str}"
slug: "{slug}"
---

"""
    return fm


# ------------------------------
#  AFFILIATE BLOCK (HTML/Markdown)
# ------------------------------

AFFILIATE_MD_BLOCK = textwrap.dedent("""
### Recommended fuel & toll partners

If you're looking for practical ways to save on fuel and road tolls across Europe, here are some partners to check out:

- [Example Fuel Card Partner](https://your-fuel-card-partner-link.com)
- [Example Toll Management Service](https://your-toll-partner-link.com)

These are affiliate links – if you sign up through them, we may earn a commission at no extra cost to you. This helps keep this site automated and free.
""").strip()


# ------------------------------
#  LLM CALL
# ------------------------------

def call_llm(prompt: str) -> str:
    """Kutsume LLM-i läbi API."""
    api_key = os.environ["LLM_API_KEY"]
    api_base = os.environ["LLM_API_BASE"]
    model = os.environ["LLM_MODEL"]

    url = f"{api_base}/chat/completions"

    headers = {"Authorization": f"Bearer {api_key}"}

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert SEO content writer specializing in trucking, "
                    "fuel cards, road tolls, logistics optimization, and EU transport regulations. "
                    "Write clear, helpful, accurate content that provides real value to readers."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 600,
        "temperature": 0.7,
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]


# ------------------------------
#  ARTICLE GENERATION
# ------------------------------

def write_article(title: str, body: str):
    slug = slugify(title)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    fm = make_front_matter(title, slug, date_str)

    # Full markdown content = front matter + body + affiliate block
    full_md = fm + "\n" + body + "\n\n" + AFFILIATE_MD_BLOCK + "\n"

    # Save file under content/posts
    filename = f"content/posts/{slug}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_md)

    print(f"Generated article: {filename}")


# ------------------------------
#  MAIN
# ------------------------------

def main():
    topic = pick_topic()

    prompt = textwrap.dedent(f"""
        Write a detailed, SEO-friendly article about:
        "{topic}"

        Requirements:
        - Minimum 800–1200 words
        - Use subheadings (###)
        - Include practical tips for trucking/fleet managers
        - Mention European context (Baltics, Poland, Germany, EU rules)
        - Provide accurate and up-to-date information
        - Do NOT invent laws or regulations; be factual
    """).strip()

    body = call_llm(prompt)
    write_article(topic, body)


if __name__ == "__main__":
    main()
