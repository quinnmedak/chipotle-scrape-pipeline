# Design: Save Firecrawl Results to knowledge/raw/

**Date:** 2026-04-15  
**Status:** Approved

## Overview

Extend `scrape_pipeline.py` to persist each Firecrawl search result as a markdown file in `knowledge/raw/` after the existing print loop.

## Filename Convention

```
knowledge/raw/YYYY-MM-DD_HH-MM-SS_<url-slug>.md
```

- The datetime is captured once before the loop so all files in a single run share the same timestamp.
- The URL slug is derived by stripping the scheme (`https://`), replacing all non-alphanumeric characters with hyphens, and collapsing repeated hyphens.
- The full datetime is always included — no collision check. Every run produces distinct files.

**Example:** `knowledge/raw/2026-04-15_14-30-22_ir-chipotle-com-news-releases.md`

## File Content

Each file begins with YAML frontmatter followed by the raw markdown from Firecrawl:

```markdown
---
title: News Releases - Chipotle Mexican Grill
url: https://ir.chipotle.com/news-releases
scraped_at: 2026-04-15T14:30:22
---

# News Releases
...
```

## Save Logic

- `knowledge/raw/` is created automatically via `Path.mkdir(parents=True, exist_ok=True)`.
- The save block is added inline inside the existing `for r in results:` loop — no new functions or modules.
- If `r['markdown']` is `None` or empty, skip writing and print a warning. No other error handling is added.

## What Is Not Changing

- The Firecrawl API call, payload, and response parsing are unchanged.
- The existing print statements are unchanged.
- No new dependencies are introduced (`datetime` and `pathlib` are stdlib).
