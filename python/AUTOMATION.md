# AKR Scout — Pipeline Automation

## GitHub Actions Setup

The scraper pipeline runs automatically via GitHub Actions. This document explains how to configure and manage it.

## Prerequisites

- A GitHub repository with your code pushed
- Supabase project URL and service_role key

## Configuring GitHub Secrets

The workflow requires two secrets to connect to Supabase.

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add each of the following:

| Secret | Value |
|--------|-------|
| `SUPABASE_URL` | Your Supabase project URL (e.g. `https://xxxxxxxxxxxx.supabase.co`) |
| `SUPABASE_SERVICE_KEY` | Your Supabase `service_role` key (from Project Settings → API) |

> **Important**: Use the `service_role` key, not the `anon` key. The scraper needs full write access to insert jobs and generate snapshots.

## How It Works

The workflow defined in `.github/workflows/scraper.yml`:

1. **Triggers** automatically every day at 06:00 UTC, or manually via **Actions** tab → **AKR Scout — Scraper Pipeline** → **Run workflow**
2. **Checks out** the repository code
3. **Sets up Python 3.12** with pip caching for fast installs
4. **Installs dependencies** from `python/requirements.txt`
5. **Installs Playwright Chromium** for headless browser scraping
6. **Injects secrets** into a `.env` file (never logged)
7. **Runs** `python main.py` with full output logging
8. **Uploads logs** as a downloadable artifact (retained 7 days)
9. **Posts a summary** to the workflow run page with status and log preview

## Triggering Manually

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Select **AKR Scout — Scraper Pipeline** in the left sidebar
4. Click **Run workflow**
5. Optionally choose a log level (DEBUG, INFO, WARNING)
6. Click **Run workflow**

## Monitoring

- Open the **Actions** tab to see all runs
- Click any run to view live logs
- Download pipeline logs from the **Artifacts** section
- The **Summary** tab shows key metrics and a log preview

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `Supabase connection failed` | Missing or invalid secrets | Check `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in GitHub Secrets |
| `Playwright` errors | Browser not installed | The workflow installs Chromium automatically |
| Pipeline timeout (>30 min) | Too many jobs or network issue | Check the logs artifact for details |
| No logs artifact | Pipeline failed before logging | Check the raw workflow logs in the Actions UI |

## Security Notes

- Secrets are never printed in logs
- The `.env` file is created at runtime and discarded when the job ends
- Logs may contain job titles and company names (public data from job boards)
- The `service_role` key grants full database access — keep it secret
