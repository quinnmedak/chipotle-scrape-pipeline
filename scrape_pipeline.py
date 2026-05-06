import os
import re
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import requests


def slugify_url(url: str) -> str:
    """Convert a URL into a filename-safe slug."""
    slug = re.sub(r'^https?://', '', url)
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


OUT_DIR = Path("knowledge/raw")


def save_results(results):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for i, r in enumerate(results, start=1):
        markdown = r.get("markdown") or ""
        if not markdown:
            print(f"  WARNING: no markdown for {r['url']}, skipping")
            continue
        slug = slugify_url(r["url"])
        filename = f"{i:02d}-{slug}.md"
        filepath = OUT_DIR / filename
        content = (
            f"---\n"
            f"title: {r['title']}\n"
            f"url: {r['url']}\n"
            f"scraped_at: {datetime.now().isoformat(timespec='seconds')}\n"
            f"---\n\n"
            f"{markdown}\n"
        )
        filepath.write_text(content, encoding="utf-8")
        print(f"  Saved: {filepath}")


load_dotenv()

api_key = os.getenv("FIRECRAWL_API_KEY")

# --- Step 01: Search + scrape with Firecrawl ---

api_url = "https://api.firecrawl.dev/v2/search"

headers = {
    "Authorization": f"Bearer {api_key}"
}

payload = {
    "query": "Chipotle investor relations press releases",
    "limit": 5,
    "scrapeOptions": {"formats": ["markdown"]}
}

if __name__ == "__main__":
    response = requests.post(api_url, headers=headers, json=payload)

    data = response.json() #convert response to json
    results = data["data"]["web"] #get results from response
    print(f"Firecrawl returned {len(results)} results")

    for r in results:
        print(f"  - {r['title']}")
        print(f"    {r['url']}")
        print(f"    markdown length: {len(r.get('markdown') or '')} chars")

    save_results(results)