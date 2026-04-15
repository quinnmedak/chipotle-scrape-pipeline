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
