# Save Firecrawl Results Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist each Firecrawl search result as a timestamped markdown file with YAML frontmatter in `knowledge/raw/`.

**Architecture:** Wrap the script body in `if __name__ == "__main__":` to allow safe importing, then add `slugify_url`, `OUT_DIR`, and `save_results` at module level in `scrape_pipeline.py`. No new modules. The `knowledge/raw/` directory is created automatically. Results with no markdown are skipped with a warning.

**Tech Stack:** Python stdlib only (`datetime`, `pathlib`, `re`) — no new dependencies.

---

## File Map

- **Modify:** `scrape_pipeline.py` — add `slugify_url()` helper and save block in the results loop
- **Create:** `tests/test_save.py` — unit tests for slug generation and file writing
- **Create:** `knowledge/raw/` — output directory (created at runtime, not committed)

---

### Task 1: Guard script body so the module is safely importable

**Files:**
- Modify: `scrape_pipeline.py` — wrap the API call and results loop in `if __name__ == "__main__":`

The test file imports `scrape_pipeline` to access `slugify_url`, `save_results`, and `OUT_DIR`. Without a guard, importing the module executes the live API call. Wrapping the script body in `if __name__ == "__main__":` fixes this.

- [ ] **Step 1: Wrap the script body**

In `scrape_pipeline.py`, indent the following block under `if __name__ == "__main__":`:

```python
if __name__ == "__main__":
    response = requests.post(api_url, headers=headers, json=payload)

    data = response.json()
    results = data["data"]["web"]
    print(f"Firecrawl returned {len(results)} results")

    for r in results:
        print(f"  - {r['title']}")
        print(f"    {r['url']}")
        print(f"    markdown length: {len(r.get('markdown') or '')} chars")
```

Everything above this block (imports, `load_dotenv()`, `api_key`, `api_url`, `headers`, `payload`) stays at module level.

- [ ] **Step 2: Verify the script still runs**

```bash
venv/bin/python scrape_pipeline.py
```

Expected: same output as before — `Firecrawl returned 5 results` followed by the 5 result lines.

- [ ] **Step 3: Commit**

```bash
git add scrape_pipeline.py
git commit -m "refactor: guard script body with __main__ for safe importing"
```

---

### Task 3: Test and implement `slugify_url`

**Files:**
- Create: `tests/test_save.py`
- Modify: `scrape_pipeline.py`

- [ ] **Step 1: Create the test file**

```python
# tests/test_save.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrape_pipeline import slugify_url

def test_slugify_basic():
    assert slugify_url("https://ir.chipotle.com/news-releases") == "ir-chipotle-com-news-releases"

def test_slugify_strips_scheme():
    assert slugify_url("https://example.com/foo/bar") == "example-com-foo-bar"

def test_slugify_collapses_hyphens():
    # query strings and multiple separators collapse cleanly
    assert slugify_url("https://example.com/a__b?q=1") == "example-com-a-b-q-1"

def test_slugify_trailing_hyphens():
    assert slugify_url("https://example.com/path/") == "example-com-path"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
venv/bin/pytest tests/test_save.py -v
```

Expected: `ImportError` or `AttributeError` — `slugify_url` does not exist yet.

- [ ] **Step 3: Add `slugify_url` to `scrape_pipeline.py`**

Add this import at the top of `scrape_pipeline.py` (after existing imports):

```python
import re
from datetime import datetime
```

Then add this function after the imports, before `load_dotenv()`:

```python
def slugify_url(url: str) -> str:
    """Convert a URL into a filename-safe slug."""
    # strip scheme
    slug = re.sub(r'^https?://', '', url)
    # replace non-alphanumeric chars with hyphens
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', slug)
    # collapse and strip edge hyphens
    slug = slug.strip('-')
    return slug
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
venv/bin/pytest tests/test_save.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add scrape_pipeline.py tests/test_save.py
git commit -m "feat: add slugify_url helper and tests"
```

---

### Task 4: Test and implement file saving

**Files:**
- Modify: `tests/test_save.py` — add file-writing tests
- Modify: `scrape_pipeline.py` — add save block in the results loop

- [ ] **Step 1: Add file-writing tests**

Append to `tests/test_save.py`:

```python
from unittest.mock import patch, MagicMock
import importlib

def _run_save_block(tmp_path, results):
    """
    Directly exercise the save logic by monkey-patching the pipeline's
    output directory and mocking the API call.
    """
    import scrape_pipeline as pipeline
    # patch OUT_DIR on the module
    with patch.object(pipeline, 'OUT_DIR', tmp_path):
        pipeline.save_results(results)

def test_save_creates_file(tmp_path):
    results = [{
        "title": "News Releases",
        "url": "https://ir.chipotle.com/news-releases",
        "markdown": "# News Releases\n\nContent here.",
    }]
    _run_save_block(tmp_path, results)
    files = list(tmp_path.glob("*.md"))
    assert len(files) == 1
    content = files[0].read_text()
    assert "title: News Releases" in content
    assert "url: https://ir.chipotle.com/news-releases" in content
    assert "# News Releases" in content

def test_save_skips_null_markdown(tmp_path, capsys):
    results = [{
        "title": "Empty Result",
        "url": "https://ir.chipotle.com/empty",
        "markdown": None,
    }]
    _run_save_block(tmp_path, results)
    files = list(tmp_path.glob("*.md"))
    assert len(files) == 0
    captured = capsys.readouterr()
    assert "skipping" in captured.out.lower() or "warning" in captured.out.lower()

def test_save_filename_format(tmp_path):
    results = [{
        "title": "SEC Filings",
        "url": "https://ir.chipotle.com/sec-filings",
        "markdown": "# SEC",
    }]
    _run_save_block(tmp_path, results)
    files = list(tmp_path.glob("*.md"))
    name = files[0].name
    # format: YYYY-MM-DD_HH-MM-SS_<slug>.md
    import re
    assert re.match(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_ir-chipotle-com-sec-filings\.md', name)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
venv/bin/pytest tests/test_save.py -v -k "save"
```

Expected: `AttributeError` — `save_results` and `OUT_DIR` don't exist yet.

- [ ] **Step 3: Add `OUT_DIR`, `save_results`, and the call site to `scrape_pipeline.py`**

After `slugify_url`, add:

```python
OUT_DIR = Path("knowledge/raw")
```

After the existing `for r in results:` print loop (after the last `print` inside the loop), add a `save_results` function and call it:

```python
def save_results(results):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    run_ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    for r in results:
        markdown = r.get("markdown") or ""
        if not markdown:
            print(f"  WARNING: no markdown for {r['url']}, skipping")
            continue
        slug = slugify_url(r["url"])
        filename = f"{run_ts}_{slug}.md"
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
```

Then at the bottom of the script, replace the existing `for r in results:` block with:

```python
print(f"Firecrawl returned {len(results)} results")

for r in results:
    print(f"  - {r['title']}")
    print(f"    {r['url']}")
    print(f"    markdown length: {len(r.get('markdown') or '')} chars")

save_results(results)
```

- [ ] **Step 4: Run all tests**

```bash
venv/bin/pytest tests/test_save.py -v
```

Expected: 7 passed.

- [ ] **Step 5: Run the pipeline end-to-end**

```bash
venv/bin/python scrape_pipeline.py
```

Expected output ends with lines like:
```
  Saved: knowledge/raw/2026-04-15_14-30-22_ir-chipotle-com-news-releases.md
  Saved: knowledge/raw/2026-04-15_14-30-22_newsroom-chipotle-com-press-releases.md
  ...
```

Verify files exist:
```bash
ls knowledge/raw/
```

Open one file and confirm frontmatter and markdown content are present.

- [ ] **Step 6: Commit**

```bash
git add scrape_pipeline.py tests/test_save.py
git commit -m "feat: save Firecrawl results as markdown files in knowledge/raw/"
```
