# GitHub Actions Scheduled Scrape Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a GitHub Actions workflow that runs the Firecrawl scrape pipeline every Monday at 7 AM UTC, commits new markdown files back to the repo, and fails fast if tests break before spending API credits.

**Architecture:** A single `scrape` job on `ubuntu-latest` runs tests then the scrape script in sequence. New files under `knowledge/raw/` are committed back using the built-in `GITHUB_TOKEN`. `FIRECRAWL_API_KEY` is injected from a GitHub repository secret.

**Tech Stack:** GitHub Actions, Python 3.11, `requests`, `python-dotenv`, `pytest`

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `requirements.txt` | Declare all runtime + test dependencies |
| Create | `.github/workflows/scrape.yml` | Define the scheduled CI/CD workflow |

---

### Task 1: Fix requirements.txt

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Replace the file contents**

  Open `requirements.txt` and replace its entire contents with:

  ```
  requests>=2.31.0
  python-dotenv>=1.0.0
  pytest>=8.0.0
  wheel==0.46.3
  ```

- [ ] **Step 2: Verify the install works**

  ```bash
  pip install -r requirements.txt
  ```

  Expected: all packages install without errors.

- [ ] **Step 3: Verify existing tests still pass**

  ```bash
  pytest tests/ -v
  ```

  Expected output (all four tests pass):
  ```
  tests/test_save.py::test_slugify_basic PASSED
  tests/test_save.py::test_slugify_strips_scheme PASSED
  tests/test_save.py::test_slugify_collapses_hyphens PASSED
  tests/test_save.py::test_slugify_trailing_hyphens PASSED
  tests/test_save.py::test_save_creates_file PASSED
  tests/test_save.py::test_save_skips_null_markdown PASSED
  tests/test_save.py::test_save_filename_format PASSED
  ```

- [ ] **Step 4: Commit**

  ```bash
  git add requirements.txt
  git commit -m "chore: add runtime and test dependencies to requirements.txt"
  ```

---

### Task 2: Create the GitHub Actions workflow

**Files:**
- Create: `.github/workflows/scrape.yml`

- [ ] **Step 1: Create the directory**

  ```bash
  mkdir -p .github/workflows
  ```

- [ ] **Step 2: Write the workflow file**

  Create `.github/workflows/scrape.yml` with this exact content:

  ```yaml
  name: Weekly Chipotle Scrape

  on:
    schedule:
      - cron: '0 7 * * 1'
    workflow_dispatch:

  jobs:
    scrape:
      runs-on: ubuntu-latest

      steps:
        - name: Checkout
          uses: actions/checkout@v4
          with:
            fetch-depth: 0

        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: '3.11'

        - name: Install dependencies
          run: pip install -r requirements.txt

        - name: Run tests
          run: pytest tests/ -v

        - name: Run scrape
          env:
            FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}
          run: python scrape_pipeline.py

        - name: Commit and push new files
          run: |
            git config user.name "github-actions[bot]"
            git config user.email "github-actions[bot]@users.noreply.github.com"
            git add knowledge/raw/
            if git diff --staged --quiet; then
              echo "No new files to commit."
            else
              git commit -m "chore: scrape run $(date +%Y-%m-%d)"
              git push origin HEAD
            fi
  ```

- [ ] **Step 3: Validate YAML syntax**

  ```bash
  python -c "import yaml; yaml.safe_load(open('.github/workflows/scrape.yml')); print('YAML OK')"
  ```

  Expected: `YAML OK`

  (If `pyyaml` is not installed: `pip install pyyaml` first.)

- [ ] **Step 4: Commit**

  ```bash
  git add .github/workflows/scrape.yml
  git commit -m "feat: add weekly GitHub Actions scrape workflow"
  ```

---

### Task 3: Add the GitHub secret (manual step)

**Files:** none — this is done in the GitHub web UI.

- [ ] **Step 1: Open your repo's secret settings**

  Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.

- [ ] **Step 2: Add the secret**

  - Name: `FIRECRAWL_API_KEY`
  - Value: your Firecrawl API key (copy from your local `.env` file)

  Click **Add secret**.

- [ ] **Step 3: Verify the secret is listed**

  The secrets list should show `FIRECRAWL_API_KEY` (value hidden). No further action needed — the workflow references it automatically.

---

### Task 4: Trigger a manual test run

- [ ] **Step 1: Push your branch to GitHub**

  ```bash
  git push origin main
  ```

- [ ] **Step 2: Trigger the workflow manually**

  Go to your GitHub repository → **Actions** → **Weekly Chipotle Scrape** → **Run workflow** → **Run workflow**.

- [ ] **Step 3: Watch the run**

  Click into the running workflow. Verify each step completes green:
  - Install dependencies ✓
  - Run tests ✓ (all 7 pass)
  - Run scrape ✓ (prints result count and filenames)
  - Commit and push new files ✓ (either commits new files or prints "No new files to commit.")

- [ ] **Step 4: Confirm files were committed (if new)**

  After the run, check the repo on GitHub. A new commit from `github-actions[bot]` should appear with message `chore: scrape run YYYY-MM-DD` and new files under `knowledge/raw/`.
