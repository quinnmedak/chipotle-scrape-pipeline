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