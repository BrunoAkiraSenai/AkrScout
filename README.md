<div align="center">
  <br/>
  <img src="screenshots/logo.svg" alt="AKR Scout" width="80" style="border-radius: 12px;"/>
  <br/>
  <h1>AKR Scout</h1>
  <h3>Intelligent Job Scouting Platform</h3>
  <br/>

  <p>
    Automated tech job aggregation · Real-time market analytics · Data-driven career insights
  </p>

  <br/>

  <!-- Badges -->
  <a href="https://github.com/anomalyco/akrscout/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/anomalyco/akrscout/scraper.yml?branch=main&style=flat-square&label=Pipeline&color=6366f1" alt="Pipeline"/>
  </a>
  <a href="https://github.com/anomalyco/akrscout">
    <img src="https://img.shields.io/badge/status-active-success?style=flat-square&color=22c55e" alt="Status"/>
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square&color=6366f1" alt="License"/>
  </a>
  <a href="https://react.dev">
    <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react" alt="React 19"/>
  </a>
  <a href="https://supabase.com">
    <img src="https://img.shields.io/badge/Supabase-PostgreSQL-3FCF8E?style=flat-square&logo=supabase" alt="Supabase"/>
  </a>
  <a href="https://tailwindcss.com">
    <img src="https://img.shields.io/badge/Tailwind-4-06B6D4?style=flat-square&logo=tailwindcss" alt="Tailwind CSS 4"/>
  </a>
  <a href="https://python.org">
    <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python" alt="Python 3.12"/>
  </a>
  <a href="https://playwright.dev">
    <img src="https://img.shields.io/badge/Playwright-Chromium-45ba4b?style=flat-square&logo=playwright" alt="Playwright"/>
  </a>
  <a href="https://vercel.com">
    <img src="https://img.shields.io/badge/deploy-Vercel-000000?style=flat-square&logo=vercel" alt="Vercel"/>
  </a>
  <a href="https://github.com/features/actions">
    <img src="https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?style=flat-square&logo=githubactions" alt="GitHub Actions"/>
  </a>

  <br/>
  <br/>

  <!-- Screenshots Row -->
  <table>
    <tr>
      <td><img src="screenshots/dashboard.svg" alt="Dashboard" width="400"/></td>
      <td><img src="screenshots/analytics.svg" alt="Analytics" width="400"/></td>
    </tr>
    <tr>
      <td align="center"><em>Dashboard — real-time market overview</em></td>
      <td align="center"><em>Analytics — skills, salary, and trends</em></td>
    </tr>
    <tr>
      <td><img src="screenshots/jobs.svg" alt="Jobs" width="400"/></td>
      <td><img src="screenshots/favorites.svg" alt="Favorites" width="400"/></td>
    </tr>
    <tr>
      <td align="center"><em>Jobs — search, filter, and scout</em></td>
      <td align="center"><em>Favorites — save and track positions</em></td>
    </tr>
  </table>

  <br/>
  <sub><strong>Built by <a href="https://github.com/anomalyco">Bruno Akira Furumori</a></strong></sub>
  <br/>
  <sub>Tech job scouting · Market intelligence · Career analytics</sub>
  <br/>
  <br/>
</div>

---

## Overview

AKR Scout is a full-stack SaaS platform that automatically aggregates, analyzes, and surfaces technology job opportunities. It combines automated web scraping with real-time analytics to provide data-driven career intelligence.

The platform scrapes tech job boards daily, normalizes listings, extracts skills, and presents everything through a premium React dashboard. Built with a clean, modular architecture and production-grade CI/CD.

### Why AKR Scout?

- **Automated** — Jobs are collected daily, no manual effort required
- **Data-driven** — Analytics reveal salary trends, skill demand, and market shifts
- **Modern stack** — React 19, Supabase, Python, all on a serverless architecture
- **Production-ready** — CI/CD, RLS security, automated pipelines, Vercel deploy

---

## Features

<table>
  <tr>
    <td width="50%">
      <h3>🤖 Automated Scraping</h3>
      <p>Daily pipeline using Playwright + BeautifulSoup. Deduplication via content hashing. Structured data extraction with skill parsing.</p>
    </td>
    <td width="50%">
      <h3>📊 Real-time Analytics</h3>
      <p>Market overview, salary by seniority, top skills, company rankings, remote vs on-site distribution. All powered by PostgreSQL aggregate views.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🔐 Authentication</h3>
      <p>Supabase Auth with email/password and OAuth (Google, GitHub). Row-Level Security ensures data isolation per user.</p>
    </td>
    <td width="50%">
      <h3>⭐ Smart Favorites</h3>
      <p>Save positions with one click. Optimistic UI updates. Syncs with the database for persistent, cross-session access.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🔍 Intelligent Filters</h3>
      <p>Search by title or company. Filter by remote, seniority level, employment type. Debounced search with pagination.</p>
    </td>
    <td width="50%">
      <h3>📱 Responsive Design</h3>
      <p>Mobile-first sidebar, adaptive layouts, touch-friendly controls. Premium dark theme with Tailwind CSS v4.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🔄 CI/CD Pipeline</h3>
      <p>GitHub Actions runs the scraper daily. Automated dependency installation, Playwright setup, and log archiving.</p>
    </td>
    <td width="50%">
      <h3>🛡️ RLS Security</h3>
      <p>Row-Level Security policies on every table. Public read for jobs, authenticated CRUD for favorites, service_role for ingestion.</p>
    </td>
  </tr>
</table>

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    RemoteOK (source)                      │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│              Python Scraper (Playwright)                   │
│                                                          │
│  1. Fetch listings       2. Parse HTML/JSON               │
│  3. Extract skills       4. Normalize data                │
│  5. Generate hash        6. Upsert to Supabase            │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│                  Supabase PostgreSQL                       │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │  jobs    │  │ companies│  │  skills  │               │
│  └──────────┘  └──────────┘  └──────────┘               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │favorites │  │job_skills│  │snapshots │               │
│  └──────────┘  └──────────┘  └──────────┘               │
│                                                          │
│  Aggregate Views: vw_jobs, vw_top_skills,                │
│  vw_top_companies, vw_remote_stats,                      │
│  vw_salary_by_seniority                                  │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│            React Frontend (Vite + Tailwind)               │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │ Dashboard│  │  Jobs    │  │Analytics │               │
│  └──────────┘  └──────────┘  └──────────┘               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │ Favorites│  │   Auth   │  │ Landing  │               │
│  └──────────┘  └──────────┘  └──────────┘               │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│                     Vercel (Deploy)                       │
└──────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Daily cron** triggers the GitHub Actions pipeline
2. **Python scraper** launches Playwright Chromium, fetches job listings
3. **HTML/JSON parsing** extracts structured data (title, company, salary, location, skills)
4. **Deduplication** via content hash — identical listings are skipped
5. **Database upsert** writes new jobs, links skills, generates analytics snapshot
6. **React app** reads from Supabase aggregate views (RLS-enforced)
7. **User** browses, searches, filters, and saves positions

---

## Tech Stack

### Frontend
| Technology | Purpose |
|-----------|---------|
| [React 19](https://react.dev) | UI library with concurrent features |
| [Vite 8](https://vitejs.dev) | Build tool and dev server |
| [Tailwind CSS v4](https://tailwindcss.com) | Utility-first styling |
| [React Router v7](https://reactrouter.com) | Client-side routing |
| [Recharts](https://recharts.org) | Composable charting library |
| [Lucide React](https://lucide.dev) | Icon library |
| [Supabase JS](https://supabase.com) | Database client and auth |

### Backend & Data
| Technology | Purpose |
|-----------|---------|
| [Supabase](https://supabase.com) | Backend-as-a-service (PostgreSQL, Auth, RLS) |
| [PostgreSQL](https://postgresql.org) | Relational database with aggregate views |
| Row-Level Security | Per-user data isolation |

### Scraping & Automation
| Technology | Purpose |
|-----------|---------|
| [Python 3.12](https://python.org) | Scraping pipeline language |
| [Playwright](https://playwright.dev) | Headless browser automation |
| [BeautifulSoup 4](https://www.crummy.com/software/BeautifulSoup/) | HTML parsing |
| [LXML](https://lxml.de) | Fast XML/HTML processing |
| [Supabase Python](https://github.com/supabase-community/supabase-py) | Database ingestion |

### DevOps
| Technology | Purpose |
|-----------|---------|
| [GitHub Actions](https://github.com/features/actions) | CI/CD and scheduled scraping |
| [Vercel](https://vercel.com) | Frontend deployment |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Environment configuration |

---

## Database

The database is a carefully designed PostgreSQL schema with 6 tables, 6 views, and 5 functions.

### Tables

| Table | Purpose |
|-------|---------|
| `companies` | Normalized company records |
| `skills` | Skill taxonomy (40+ tech skills) |
| `jobs` | Job listings with content hash dedup |
| `job_skills` | Many-to-many job-to-skill mapping |
| `favorites` | User-specific saved jobs (RLS-enforced) |
| `analytics_snapshots` | Time-series market data |

### Views

| View | Purpose |
|------|---------|
| `vw_jobs` | Enriched job listings with company name and skills |
| `vw_recent_jobs` | Jobs from the last 7 days |
| `vw_top_skills` | Skill demand ranking |
| `vw_top_companies` | Company hiring frequency |
| `vw_remote_stats` | Remote vs on-site distribution |
| `vw_salary_by_seniority` | Average salary ranges per seniority level |

### Functions

- `fn_generate_job_hash` — SHA-256 deduplication hash
- `fn_toggle_favorite` — Safe favorite add/remove
- `fn_upsert_job` — Idempotent job insertion
- `fn_set_job_skills` — Batch skill association

### Security

- **Public**: Read access to `jobs`, `companies`, `skills` (authenticated users)
- **Authenticated**: Full CRUD on `favorites` (scoped to `auth.uid()`)
- **Service Role**: Full write access for the scraper pipeline

---

## Automation

### GitHub Actions Pipeline

The scraper runs automatically every day at 06:00 UTC via a GitHub Actions workflow.

```
┌──────────────────────────────────────────┐
│  Schedule: 0 6 * * * (daily)             │
│  Manual: workflow_dispatch (anytime)     │
├──────────────────────────────────────────┤
│  1. Checkout repository                  │
│  2. Setup Python 3.12 (cached)           │
│  3. Install dependencies                 │
│  4. Install Playwright Chromium          │
│  5. Inject Supabase secrets              │
│  6. Run python main.py                   │
│  7. Upload logs as artifact              │
│  8. Post summary to run page             │
└──────────────────────────────────────────┘
```

- **30-minute timeout** prevents runaway executions
- **Logs retained** for 7 days as downloadable artifacts
- **Summary page** shows status, duration, and log preview
- **Manual trigger** supports DEBUG/INFO/WARNING log levels

---

## Screenshots

<table>
  <tr>
    <td><img src="screenshots/dashboard.svg" alt="Dashboard" width="400"/></td>
    <td><img src="screenshots/analytics.svg" alt="Analytics" width="400"/></td>
  </tr>
  <tr>
    <td align="center"><strong>Dashboard</strong> — Market overview with stats, top skills, company rankings</td>
    <td align="center"><strong>Analytics</strong> — Salary by seniority, remote vs on-site, skill trends</td>
  </tr>
  <tr>
    <td><img src="screenshots/jobs.svg" alt="Jobs" width="400"/></td>
    <td><img src="screenshots/favorites.svg" alt="Favorites" width="400"/></td>
  </tr>
  <tr>
    <td align="center"><strong>Jobs</strong> — Search, filter by seniority/remote, pagination</td>
    <td align="center"><strong>Favorites</strong> — Saved positions with quick access</td>
  </tr>
  <tr>
    <td><img src="screenshots/login.svg" alt="Login" width="400"/></td>
    <td><img src="screenshots/mobile.svg" alt="Mobile" width="400"/></td>
  </tr>
  <tr>
    <td align="center"><strong>Authentication</strong> — Supabase Auth with OAuth providers</td>
    <td align="center"><strong>Mobile</strong> — Responsive design with collapsible sidebar</td>
  </tr>
</table>

> Screenshots will be added as the project evolves. Placeholder files are in the `screenshots/` directory.

---

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.12+
- A Supabase project (free tier works)
- Playwright browser support

### Frontend Setup

```bash
# Clone the repository
git clone https://github.com/anomalyco/akrscout.git
cd akrscout/frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials

# Start development server
npm run dev
```

### Scraper Setup

```bash
cd akrscout/python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your Supabase service role key

# Run the scraper
python main.py
```

### Database Setup

Run the SQL schema against your Supabase project:

```bash
# Connect to your Supabase SQL editor and paste:
# supabase/schema.sql
```

Or use the Supabase CLI:

```bash
supabase db push
```

---

## Environment Variables

### Frontend (`frontend/.env`)

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```

### Python Scraper (`python/.env`)

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
```

> **Never commit `.env` files.** The repository includes `.env.example` templates with placeholder values. The GitHub Actions workflow injects secrets at runtime via GitHub Secrets.

---

## Engineering Highlights

<details>
<summary><strong>Clean Architecture</strong> — Modular separation of concerns</summary>

<br/>

The frontend follows a strict layered architecture:
- **services/** — Supabase client, API abstraction
- **hooks/** — Custom hooks encapsulate all data fetching (useJobs, useAnalytics, useFavorites)
- **contexts/** — Auth state, notification system
- **components/** — Reusable UI primitives (StatCard, ChartCard, JobCard, Skeleton)
- **pages/** — Route-level components compose hooks + components
- **routes/** — Centralized routing with auth guards

This makes the codebase predictable, testable, and easy to navigate.
</details>

<details>
<summary><strong>Modular Pipeline</strong> — Extensible scraper architecture</summary>

<br/>

The Python scraper uses an abstract base class pattern:
- **BaseScraper** — ABC defining the scraper contract
- **RemoteOKScraper** — Concrete implementation for RemoteOK
- **Parser layer** — Separates HTML parsing from fetching
- **Service layer** — Database operations isolated in DatabaseService
- **Tracker** — Pipeline instrumentation and metrics

Adding a new job source requires only a new scraper class implementing `fetch()` and `parse()`.
</details>

<details>
<summary><strong>Reusable Hooks</strong> — Custom React hooks for data access</summary>

<br/>

All Supabase queries are encapsulated in custom hooks:
- `useJobs()` — Paginated job list with search, filters, sorting
- `useAnalytics()` — Parallel fetches for all chart data
- `useFavorites()` — Optimistic UI with Set-based cache and favorites sync
- `useAuth()` — Session management with Supabase Auth
- `useTheme()` — Dark mode with localStorage persistence
- `useSEO()` — Dynamic document title and meta tags
</details>

<details>
<summary><strong>Scalable Database</strong> — PostgreSQL with aggregate views</summary>

<br/>

Database design prioritizes query performance:
- **Materialized-like views** — Pre-joined aggregates for dashboard queries
- **Content hash index** — O(1) deduplication via `fn_generate_job_hash`
- **RLS policies** — Row-level security without application overhead
- **Batch operations** — `fn_set_job_skills` handles bulk skill associations

The view layer (`vw_*`) abstracts complex joins so the frontend queries simple, flat structures.
</details>

<details>
<summary><strong>Production-ready Frontend</strong> — Premium UX and performance</summary>

<br/>

- **React 19** with memoized components (`React.memo`, `useCallback`, `useMemo`)
- **Debounced search** (300ms) to reduce Supabase query volume
- **Optimistic UI** for favorites — instant feedback, async sync
- **Skeleton loading** with shimmer animation for every page
- **Toast notifications** for user actions (favorites, auth, errors)
- **Error boundaries** with retry capability
- **Responsive design** — mobile-first sidebar with overlay drawer
- **SEO** — Dynamic meta tags, Open Graph, descriptive titles
</details>

<details>
<summary><strong>CI/CD</strong> — Automated testing and deployment</summary>

<br/>

- **GitHub Actions** runs the scraper daily at 06:00 UTC
- **Vercel** deploys the frontend automatically on push to main
- **Artifact logging** retains 7 days of pipeline logs
- **Secrets management** via GitHub Secrets (never in code)
- **Manual trigger** supports log level selection (DEBUG/INFO/WARNING)
</details>

---

## Roadmap

- [x] Automated job scraping
- [x] Real-time analytics dashboard
- [x] User authentication and favorites
- [x] CI/CD pipeline with daily automation
- [x] Responsive mobile experience
- [ ] **AI-powered recommendations** — Match jobs to user profiles
- [ ] **Salary insights** — Historical salary trends and projections
- [ ] **Skill trend forecasting** — ML-based demand prediction
- [ ] **Email notifications** — Daily digest of new matching positions
- [ ] **Multi-source scraping** — LinkedIn, Indeed, Wellfound, etc.
- [ ] **Chrome extension** — One-click save from any job board

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<br/>
<div align="center">
  <sub>
    <strong>Developed by Bruno Akira Furumori</strong>
    <br/>
    <a href="https://github.com/anomalyco">GitHub</a> ·
    <a href="https://linkedin.com/in/bruno-akira-furumori">LinkedIn</a>
    <br/>
    <br/>
    <img src="https://img.shields.io/badge/Made%20with-React%20%7C%20Supabase%20%7C%20Python-6366f1?style=flat-square" alt="Made with"/>
    <br/>
    <br/>
    <img src="screenshots/logo.svg" alt="AKR Scout" width="32" style="border-radius: 6px;"/>
    <br/>
    <sub>© 2026 AKR Scout. Intelligent job scouting platform.</sub>
  </sub>
</div>
<br/>
