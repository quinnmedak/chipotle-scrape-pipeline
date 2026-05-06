import re
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


from unittest.mock import patch

def _run_save_block(tmp_path, results):
    import scrape_pipeline as pipeline
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
    assert re.match(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_01-ir-chipotle-com-sec-filings\.md', name)
