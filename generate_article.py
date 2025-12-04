import os
import re
import textwrap
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import requests
from requests.exceptions import RequestException


# ------------------------------
#  PATHS
# ------------------------------

BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content" / "posts"


# ------------------------------
#  LOGISTICS / FUEL COST NICHE
#  (fallback-teemad, kui LLM-i põhine valik ei tööta)
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


# ------------------------------
#  FRONT MATTER / SLUG
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
#  AFFILIATE BLOCK (Markdown)
# ------------------------------

AFFILIATE_MD_BLOCK = textwrap.dedent("""
### Recommended fuel & toll partners

If you're looking for practical ways to save on fuel and road tolls across Europe, here are some partners to check out:

- [Example Fuel Card Partner](https://your-fuel-card-partner-link.com)
- [Example Toll Management Service](https://your-toll-partner-link.com)

These are affiliate links – if you sign up through them, we may earn a commission at no extra cost to you.
""").strip()


# ------------------------------
#  LLM HELPERS + RETRIES
# ------------------------------

def _get_llm_config() -> Dict[str, str]:
    return {
        "api_key": os.environ["LLM_API_KEY"],
        "api_base": os.environ["LLM_API_BASE"],
        "model": os.environ["LLM_MODEL"],
    }


def _post_with_retries(url: str, headers: Dict[str, str], payload: Dict, max_retries: int = 3, timeout: int = 60) -> requests.Response:
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=timeout)

            if resp.status_code in (429,) or resp.status_code >= 500:
                # rate limit või serveri viga – proovime uuesti
                print(f"[LLM] HTTP {resp.status_code}, retry {attempt}/{max_retries}")
                last_exc = Exception(f"Bad status {resp.status_code}: {resp.text[:200]}")
            else:
                return resp

        except RequestException as e:
            print(f"[LLM] Request error on attempt {attempt}/{max_retries}: {e}")
            last_exc = e

        if attempt < max_retries:
            sleep_s = 3 * attempt
            print(f"[LLM] Sleeping {sleep_s} seconds before retry...")
            time.sleep(sleep_s)

    # Kui siia jõuame, on kõik katsed läbi kukkunud
    if last_exc:
        raise last_exc
    raise RuntimeError("Unknown LLM error")


def call_llm_for_article(prompt: str) -> str:
    """Kutsume LLM-i artikli kirjutamiseks koos retrydega."""
    cfg = _get_llm_config()
    url = f"{cfg['api_base']}/chat/completions"
    headers = {"Authorization": f"Bearer {cfg['api_key']}"}

    payload = {
        "model": cfg["model"],
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert SEO content writer specializing in trucking, "
                    "fuel cards, road tolls, logistics optimization, and EU transport regulations. "
                    "You optimise content for high commercial intent and conversions, "
                    "encouraging readers to compare providers or contact service partners."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 900,
        "temperature": 0.7,
    }

    resp = _post_with_retries(url, headers, payload, max_retries=3, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def call_llm_for_topic(existing_titles: List[str], year: int) -> str:
    """
    Palume LLM-il pakkuda UUE SEO-artikli pealkirja,
    arvestades juba olemasolevaid pealkirju ja maksimeerides
    võimaliku tulu (affiliate / leadid).
    """
    cfg = _get_llm_config()
    url = f"{cfg['api_base']}/chat/completions"
    headers = {"Authorization": f"Bearer {cfg['api_key']}"}

    existing_titles_text = "\n".join(f"- {t}" for t in existing_titles[:50]) or "(no existing articles yet)"

    user_prompt = textwrap.dedent(f"""
        You help plan highly profitable SEO content for a niche website.
        Niche: European trucking companies (focus on Baltics), fuel cards, diesel savings, road tolls
        (especially Poland and Germany), EU compliance, fleet management and cash-flow optimisation.

        Current year: {year}.

        Here is a list of article titles we have ALREADY published:
        {existing_titles_text}

        Your task:
        - Propose EXACTLY ONE new SEO-friendly article title.
        - It must have HIGH COMMERCIAL INTENT and strong monetisation potential
          (e.g. comparing providers, fuel cards, toll devices, payment terms, fines help).
        - It must NOT duplicate or be nearly identical to the existing titles.
        - It should be specific and attractive for fleet managers or transport company owners.
        - Output ONLY the raw title text, nothing else. No quotes, no explanations.
    """).strip()

    payload = {
        "model": cfg["model"],
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an SEO and monetisation strategist for a trucking and logistics niche website. "
                    "You only output clean, ready-to-use article titles optimised for high revenue potential."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 80,
        "temperature": 0.85,
    }

    resp = _post_with_retries(url, headers, payload, max_retries=3, timeout=60)
    resp.raise_for_status()
    title = resp.json()["choices"][0]["message"]["content"]
    return title.strip().strip('"').strip("'").strip()


# ------------------------------
#  EXISTING TITLES
# ------------------------------

def extract_title_from_front_matter(text: str) -> str | None:
    m = re.search(r'^title:\s*"(.*?)"\s*$', text, re.MULTILINE)
    if m:
        return m.group(1)
    m2 = re.search(r"^title:\s*'(.*?)'\s*$", text, re.MULTILINE)
    if m2:
        return m2.group(1)
    return None


def get_existing_titles() -> List[str]:
    titles: List[str] = []
    if not CONTENT_DIR.exists():
        return titles

    for path in CONTENT_DIR.glob("*.md"):
        try:
            raw = path.read_text(encoding="utf-8")
        except Exception:
            continue

        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.DOTALL)
        if not fm_match:
            continue
        fm_text = fm_match.group(1)
        title = extract_title_from_front_matter(fm_text)
        if title:
            titles.append(title.strip())

    return titles


# ------------------------------
#  TOPIC PICKER (AUTONOOMNE)
# ------------------------------

def pick_topic() -> str:
    """
    Püüab esmalt LLM-iga genereerida uue unikaalse ja tulusa teema.
    Kui midagi läheb valesti, kasutab TOPIC_TEMPLATES fallback'i.
    """
    year = datetime.now(timezone.utc).year
    existing_titles = get_existing_titles()

    try:
        new_title = call_llm_for_topic(existing_titles, year)
        if not new_title:
            raise ValueError("LLM returned empty title")

        new_title_lower = new_title.lower()
        for t in existing_titles:
            if new_title_lower == t.lower():
                raise ValueError("LLM returned duplicate title")

        return new_title

    except Exception as e:
        print(f"[pick_topic] LLM topic generation failed, falling back to templates. Reason: {e}")
        template = random.choice(TOPIC_TEMPLATES)
        return template.format(year=year)


# ------------------------------
#  ARTICLE GENERATION
# ------------------------------

def write_article(title: str, body: str):
    slug = slugify(title)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    fm = make_front_matter(title, slug, date_str)

    full_md = fm + "\n" + body + "\n\n" + AFFILIATE_MD_BLOCK + "\n"

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    filename = CONTENT_DIR / f"{slug}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_md)

    print(f"Generated article: {filename}")


def main():
    year = datetime.now(timezone.utc).year
    topic = pick_topic()
    print(f"Using topic: {topic!r}")

    prompt = textwrap.dedent(f"""
        Write a detailed, SEO-friendly article about:
        "{topic}"

        Requirements:
        - Minimum 800–1200 words
        - Use subheadings (###)
        - Include practical, actionable tips for trucking/fleet managers
        - Mention European context (Baltics, Poland, Germany, EU rules) where relevant
        - Provide accurate and conservative information relevant to year {year}
        - Optimise for conversions: naturally encourage readers to compare fuel card or toll providers
          and consider contacting a service partner for help.
        - Do NOT invent specific laws or regulations; if unsure, stay high-level and conservative.
    """).strip()

    body = call_llm_for_article(prompt)
    write_article(topic, body)


if __name__ == "__main__":
    main()
