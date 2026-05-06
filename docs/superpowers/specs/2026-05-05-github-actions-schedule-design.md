# Design: GitHub Actions Scheduled Scrape Pipeline

**Date:** 2026-05-05
**Status:** Approved

## Overview

Add a GitHub Actions workflow that runs `scrape_pipeline.py` on a weekly schedule, commits the resulting markdown files back to the repository, and fails fast if the test suite breaks before spending API credits.

## Trigger & Schedule

File: `.github/workflows/scrape.yml`

Two triggers:
- `schedule`: cron `0 7 * * 1` — every Monday at 7 AM UTC (2 AM Eastern, before market open), capturing any weekend announcements and providing a fresh weekly snapshot of Chipotle IR content.
- `workflow_dispatch`: manual trigger from the GitHub Actions UI for on-demand runs mid-week if a major announcement drops.

**Rationale for weekly cadence:** Chipotle IR press releases and SEC filings are published at most a few times per week, typically around market events. Daily runs would burn 7× more Firecrawl API credits for content that barely changes. Monthly is too coarse — a full earnings cycle could be missed. Weekly at Monday morning is the sweet spot.

## Job Architecture

Single job (`scrape`) running on `ubuntu-latest`. Linear steps — no job splitting, no matrix. Tests and scrape share the same workspace so no artifact passing is needed.

## Steps

1. **Checkout** — `actions/checkout@v4` with `fetch-depth: 0` so the bot commit can be pushed back to the repo.
2. **Set up Python** — `actions/setup-python@v5`, version `3.11`.
3. **Install dependencies** — `pip install -r requirements.txt` (requires fixing `requirements.txt` to include `requests`, `python-dotenv`, and `pytest`).
4. **Run tests** — `pytest tests/` with default settings. Fails fast; the scrape step is skipped if tests fail, preventing wasted API credits.
5. **Run scrape** — `python scrape_pipeline.py` with `FIRECRAWL_API_KEY` injected as an environment variable from GitHub secrets.
6. **Commit & push** — checks `git status` for new files under `knowledge/raw/`; if any exist, commits with message `chore: scrape run YYYY-MM-DD` and pushes using `GITHUB_TOKEN`. No-op if scrape produced no new files.

## Secrets & Environment

- `FIRECRAWL_API_KEY`: stored as a GitHub Actions repository secret; injected via `env:` on the scrape step only. Never appears in logs.
- `GITHUB_TOKEN`: provided automatically by GitHub Actions; used to push the commit back. No personal access token required.
- Git commit identity set to `github-actions[bot] <github-actions[bot]@users.noreply.github.com>` so automated commits are visually distinct in history.
- `.env` file remains gitignored and is never used in CI.

## What Is Not Changing

- `scrape_pipeline.py` logic is unchanged.
- The `knowledge/raw/` filename convention and frontmatter format are unchanged.
- Existing tests are unchanged.

## Files Added or Modified

- `.github/workflows/scrape.yml` — new workflow file
- `requirements.txt` — updated to include `requests`, `python-dotenv`, `pytest`
