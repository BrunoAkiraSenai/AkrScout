import asyncio
import json
import re
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

from config.settings import (
    GOOGLE_JOBS_QUERIES,
    GOOGLE_JOBS_MAX_JOBS,
    GOOGLE_JOBS_DELAY_MIN,
    GOOGLE_JOBS_DELAY_MAX,
    GOOGLE_JOBS_LANG,
    GOOGLE_JOBS_COUNTRY,
)
from parsers.skill_extractor import SkillExtractor
from services.supabase import DatabaseService
from utils.logger import setup_logger
from utils.normalizer import clean_html, parse_salary, truncate

from .base import BaseScraper, ScrapedJob

logger = setup_logger("google_jobs")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


class GoogleJobsScraper(BaseScraper):
    def __init__(self, db: DatabaseService):
        self._db = db
        self._skill_extractor = SkillExtractor()
        self._collected: List[Dict[str, Any]] = []

    def source_name(self) -> str:
        return "google_jobs"

    def _random_delay(self, min_s: float = None, max_s: float = None) -> float:
        return random.uniform(min_s or GOOGLE_JOBS_DELAY_MIN, max_s or GOOGLE_JOBS_DELAY_MAX)

    async def _search_query(self, query: str) -> List[Dict[str, Any]]:
        params = {
            "q": f"{query} brasil vaga",
            "ibp": "htl;jobs",
            "gl": GOOGLE_JOBS_COUNTRY,
            "hl": GOOGLE_JOBS_LANG,
        }
        url = f"https://www.google.com/search?{urlencode(params)}"
        logger.info("Google Jobs URL: %s", url)

        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": f"{GOOGLE_JOBS_LANG},{GOOGLE_JOBS_COUNTRY.lower()};q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
        }

        try:
            async with AsyncSession(impersonate="chrome124") as session:
                resp = await session.get(url, timeout=30, headers=headers)
                logger.debug("Google response status=%d size=%d for '%s'", resp.status_code, len(resp.text), query)

                if resp.status_code != 200:
                    logger.warning("Google returned status %d for '%s'", resp.status_code, query)
                    return []

                text = resp.text
                preview = text[:3000].replace('\n', ' ')[:600]
                logger.info("Google HTML preview: %s", preview)

                lower = text.lower()
                if "captcha" in lower or "unusual traffic" in lower:
                    logger.warning("Google CAPTCHA/blocking detected for '%s'", query)
                    return []
                if "before you continue" in lower or "consent" in lower or "cookies" in lower:
                    logger.warning("Google cookie consent page for '%s'", query)
                    return []
                if "enable javascript" in lower or "javascript" in lower:
                    logger.warning("Google requires JavaScript for '%s'", query)

                json_ld_count = len(text.split('"application/ld+json"'))
                logger.debug("JSON-LD script tags found: %d", json_ld_count - 1)

                return self._parse_results(text, query)
        except Exception as e:
            logger.warning("Google Jobs request failed for '%s': %s", query, e)
            return []

    def _parse_results(self, html: str, query: str) -> List[Dict[str, Any]]:
        total_len = len(html)
        has_json_ld = 'application/ld+json' in html
        has_jobs_class = 'gws-plugins-horizon-jobs' in html

        logger.debug("Parsing: size=%d, has_json_ld=%s, has_jobs_class=%s", total_len, has_json_ld, has_jobs_class)

        if has_json_ld:
            try:
                data = self._extract_json_ld(html)
                if data:
                    logger.info("JSON-LD extraction found %d jobs for '%s'", len(data), query)
                    return data
            except Exception as e:
                logger.debug("JSON-LD extraction failed: %s", e)

        try:
            data = self._extract_html_bs4(html)
            if data:
                logger.info("HTML extraction found %d jobs for '%s'", len(data), query)
                return data
        except Exception as e:
            logger.debug("BeautifulSoup extraction failed: %s", e)

        logger.info("No jobs found for '%s' (size=%d, json_ld=%s)", query, total_len, has_json_ld)
        return []

    def _extract_json_ld(self, html: str) -> List[Dict[str, Any]]:
        cards = []
        soup = BeautifulSoup(html, "lxml")
        scripts = soup.find_all("script", type="application/ld+json")
        logger.debug("Found %d JSON-LD script tags", len(scripts))

        for script in scripts:
            try:
                content = script.string
                if not content or not content.strip():
                    continue
                data = json.loads(content)
            except (json.JSONDecodeError, TypeError) as e:
                logger.debug("JSON-LD parse error: %s", e)
                continue

            items = []
            if isinstance(data, dict):
                if data.get("@type") == "ItemList":
                    items = data.get("itemListElement", [])
                    items = [it.get("item", it) for it in items] if items else data.get("items", [])
                elif data.get("@type") == "JobPosting":
                    items = [data]

            logger.debug("JSON-LD block with %d potential items (type=%s)", len(items),
                         data.get("@type", "unknown") if isinstance(data, dict) else "list")

            for job in items:
                if not isinstance(job, dict):
                    continue
                if job.get("@type") not in ("JobPosting", "Job"):
                    continue
                try:
                    parsed = self._parse_ld_job(job)
                    if parsed:
                        cards.append(parsed)
                except Exception as e:
                    logger.debug("JSON-LD job parse error: %s", e)
                    continue

        logger.debug("JSON-LD extracted %d jobs total", len(cards))
        return cards

    def _parse_ld_job(self, job: dict) -> Optional[Dict[str, Any]]:
        title = job.get("title", "").strip()
        if not title:
            return None

        org = job.get("hiringOrganization", {})
        if isinstance(org, dict):
            company = org.get("name", "")
        else:
            company = org or "Unknown"

        location = ""
        loc = job.get("jobLocation", {})
        if isinstance(loc, dict):
            addr = loc.get("address", {})
            if isinstance(addr, dict):
                parts = [addr.get("addressLocality", ""), addr.get("addressRegion", "")]
                location = ", ".join(p for p in parts if p)

        desc = clean_html(job.get("description", "")) or ""

        salary_min, salary_max = None, None
        salary = job.get("baseSalary", {})
        if isinstance(salary, dict):
            value = salary.get("value", {})
            if isinstance(value, dict):
                salary_min = value.get("minValue")
                salary_max = value.get("maxValue")
            elif isinstance(value, (int, float)):
                salary_min = value
            currency = salary.get("currency", "BRL")

        posted_at = job.get("datePosted", "")

        remote = any(w in title.lower() for w in ["remoto", "remote", "home office", "home-office"]) or \
                 any(w in desc.lower() for w in ["remoto", "remote", "home office", "home-office"])

        direct_apply = job.get("directApply", False)
        job_url = job.get("url", "")

        return {
            "title": title,
            "company": company,
            "location": location,
            "remote": remote,
            "description": desc,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_text": "",
            "detail_url": job_url,
            "posted_at": posted_at,
            "direct_apply": direct_apply,
        }

    def _extract_html_bs4(self, html: str) -> List[Dict[str, Any]]:
        cards = []
        soup = BeautifulSoup(html, "lxml")
        seen = set()

        job_selectors = [
            {"card": "div[class*='job-card'], div[class*='gws-plugins-horizon-jobs']",
             "title": "h3, h2[class*='title'], div[class*='title']",
             "company": "div[class*='company'], span[class*='company'], div[class*='employer']",
             "location": "div[class*='location'], span[class*='location'], div[class*='loc']",
             "salary": "div[class*='salary'], span[class*='salary']",
             "date": "div[class*='date'], span[class*='date'], div[class*='age']"},
            {"card": "div[data-result-index], div[jsname]",
             "title": "h3, a[href*='jobs']",
             "company": "div[class*='Qk80vf'], span[class*='Qk80vf']",
             "location": "div[class*='ragvQd'], span[class*='ragvQd']",
             "salary": "div[class*='QYpI6c'], span[class*='QYpI6c']",
             "date": "div[class*='K5hUy'], span[class*='K5hUy']"},
        ]

        for sel in job_selectors:
            try:
                containers = soup.select(sel["card"])
                if not containers:
                    continue
                for container in containers:
                    try:
                        title_el = container.select_one(sel["title"])
                        if not title_el:
                            continue
                        title = title_el.get_text(strip=True)
                        if not title or title in seen:
                            continue
                        seen.add(title)

                        link = container.select_one("a")
                        job_url = link.get("href", "") if link else ""
                        if job_url and not job_url.startswith("http"):
                            job_url = "https://www.google.com" + job_url

                        company = ""
                        company_el = container.select_one(sel["company"])
                        if company_el:
                            company = company_el.get_text(strip=True)

                        location = ""
                        loc_el = container.select_one(sel["location"])
                        if loc_el:
                            location = loc_el.get_text(strip=True)

                        salary_text = ""
                        salary_el = container.select_one(sel["salary"])
                        if salary_el:
                            salary_text = salary_el.get_text(strip=True)

                        date_text = ""
                        date_el = container.select_one(sel["date"])
                        if date_el:
                            date_text = date_el.get_text(strip=True)

                        remote = "remoto" in title.lower() or "home office" in title.lower() or \
                                 "remoto" in location.lower() or "home office" in location.lower()

                        cards.append({
                            "title": title,
                            "company": company,
                            "location": location,
                            "remote": remote,
                            "description": "",
                            "salary_min": None,
                            "salary_max": None,
                            "salary_text": salary_text,
                            "detail_url": job_url,
                            "posted_at": self._parse_relative_date(date_text),
                            "direct_apply": False,
                        })

                        if len(cards) >= GOOGLE_JOBS_MAX_JOBS:
                            return cards
                    except Exception:
                        continue
                if cards:
                    break
            except Exception:
                continue

        return cards

    def _parse_relative_date(self, text: str) -> Optional[str]:
        if not text:
            return None
        text_lower = text.lower().strip()
        now = datetime.now(timezone.utc)

        patterns = [
            (r"há\s*(\d+)\s*(minuto|hora|dia|semana|mês|mes|ano)", "pt"),
            (r"(\d+)\s*(minute|hour|day|week|month|year)\s*ago", "en"),
            (r"(today|now|just now|moments ago)", "en_now"),
            (r"(hoje|agora|momentos atrás|agora mesmo)", "pt_now"),
            (r"há\s*(\d+)\s*(minutos|horas|dias|semanas|meses|anos)", "pt"),
            (r"(\d+)\s+(minutes?|hours?|days?|weeks?|months?|years?)", "en"),
        ]

        for pattern, lang in patterns:
            match = re.search(pattern, text_lower)
            if match:
                if lang in ("en_now", "pt_now"):
                    return now.isoformat()
                amount = int(match.group(1))
                unit = match.group(2).lower()
                if unit in ("minuto", "minutos", "minute", "minutes"):
                    dt = now.replace(hour=now.hour - amount)
                elif unit in ("hora", "horas", "hour", "hours"):
                    dt = now.replace(hour=now.hour - amount)
                elif unit in ("dia", "dias", "day", "days"):
                    dt = now.replace(day=now.day - amount)
                elif unit in ("semana", "semanas", "week", "weeks"):
                    dt = now.replace(day=now.day - amount * 7)
                elif unit in ("mês", "mes", "mês", "meses", "month", "months"):
                    dt = now.replace(day=now.day - amount * 30)
                elif unit in ("ano", "anos", "year", "years"):
                    dt = now.replace(day=now.day - amount * 365)
                else:
                    dt = now
                return dt.isoformat()
        return None

    async def _needs_javascript(self, html: str) -> bool:
        return "enable javascript" in html.lower() or "/enablejs" in html

    async def _search_with_playwright(self, query: str) -> List[Dict[str, Any]]:
        from playwright.async_api import async_playwright

        params = {
            "q": f"{query} brasil vaga",
            "ibp": "htl;jobs",
            "gl": GOOGLE_JOBS_COUNTRY,
            "hl": GOOGLE_JOBS_LANG,
        }
        url = f"https://www.google.com/search?{urlencode(params)}"
        logger.info("Playwright Google Jobs URL: %s", url)

        async with async_playwright() as pw:
            launch_opts = {
                "headless": True,
                "args": [
                    "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            }
            try:
                launch_opts["channel"] = "chrome"
                browser = await pw.chromium.launch(**launch_opts)
            except Exception:
                launch_opts.pop("channel", None)
                browser = await pw.chromium.launch(**launch_opts)

            try:
                context = await browser.new_context(
                    user_agent=random.choice(USER_AGENTS),
                    viewport={"width": 1920, "height": 1080},
                    locale="pt-BR",
                    timezone_id="America/Sao_Paulo",
                )
                page = await context.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                try:
                    await page.wait_for_selector(
                        "div[class*='job-card'], div[id*='jobs'], div[data-docid], div[jsname]",
                        timeout=15000
                    )
                except Exception:
                    pass

                await asyncio.sleep(3)

                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, 500)")
                    await asyncio.sleep(1)

                html = await page.content()
                logger.debug("Playwright HTML size: %d for '%s'", len(html), query)

                cards = self._parse_results(html, query)
                logger.info("Playwright found %d jobs for '%s'", len(cards), query)
                return cards
            finally:
                await browser.close()

    async def fetch_raw(self) -> List[Dict[str, Any]]:
        self._collected = []
        logger.info("Google Jobs scraping started (%d queries)", len(GOOGLE_JOBS_QUERIES))

        needs_playwright = False
        for query in GOOGLE_JOBS_QUERIES:
            if len(self._collected) >= GOOGLE_JOBS_MAX_JOBS:
                break
            logger.info("Searching Google Jobs for: %s", query)
            cards = await self._search_query(query)
            logger.info("Google Jobs found %d raw entries for '%s'", len(cards), query)
            for card in cards:
                if len(self._collected) >= GOOGLE_JOBS_MAX_JOBS:
                    break
                self._collected.append(card)
                await asyncio.sleep(self._random_delay())
            if not cards:
                needs_playwright = True

        if needs_playwright:
            logger.info("curl_cffi returned no results, trying Playwright for JavaScript rendering")
            for query in GOOGLE_JOBS_QUERIES:
                if len(self._collected) >= GOOGLE_JOBS_MAX_JOBS:
                    break
                logger.info("Playwright search for: %s", query)
                cards = await self._search_with_playwright(query)
                for card in cards:
                    if len(self._collected) >= GOOGLE_JOBS_MAX_JOBS:
                        break
                    self._collected.append(card)
                    await asyncio.sleep(self._random_delay())

        logger.info("Google Jobs collected %d raw entries total", len(self._collected))
        return self._collected

    def _infer_seniority(self, title: str, description: str) -> Optional[str]:
        text = (title + " " + (description or "")).lower()
        if any(w in text for w in ["junior", "jr", "júnior", "entry", "entry-level", "trainee", "estágio", "estagiario", "estagiário", "graduate", "juniors"]):
            return "junior"
        if any(w in text for w in ["pleno", "mid", "intermediate", "mid-level", "middle"]):
            return "mid"
        if any(w in text for w in ["senior", "sr", "sênior", "sénior", "staff", "principal", "lead", "tech lead", "head of", "coordenador", "coordenadora", "especialista"]):
            return "senior"
        return None

    def _infer_employment_type(self, title: str, description: str) -> Optional[str]:
        text = (title + " " + (description or "")).lower()
        if any(w in text for w in ["part time", "part-time", "meio periodo", "meio período"]):
            return "part_time"
        if any(w in text for w in ["contract", "freelance", "freela", "pj", "temporary", "temp", "autônomo", "autonomo"]):
            return "contract"
        if any(w in text for w in ["intern", "internship", "estágio", "estagiario", "estagiário", "trainee"]):
            return "internship"
        return "full_time"

    def _extract_tags(self, title: str, description: str) -> List[str]:
        tags = []
        tech_keywords = [
            "python", "javascript", "typescript", "react", "node", "nodejs",
            "java", "go", "golang", "rust", "c#", "csharp", ".net",
            "php", "ruby", "rails", "swift", "kotlin", "flutter",
            "angular", "vue", "vuejs", "nextjs", "next.js",
            "aws", "azure", "gcp", "docker", "kubernetes", "k8s",
            "terraform", "ansible", "jenkins", "gitlab", "github actions",
            "postgresql", "postgres", "mysql", "mongodb", "redis",
            "elasticsearch", "kafka", "rabbitmq", "graphql",
            "machine learning", "deep learning", "data science", "ai",
            "react native", "tailwind", "sass", "less", "webpack",
            "linux", "bash", "shell", "sql", "nosql", "api", "rest",
            "microservices", "ci/cd", "devops", "sre",
            "frontend", "backend", "fullstack", "full stack",
            "agile", "scrum", "git", "github",
        ]
        corpus = (title + " " + description).lower()
        for kw in tech_keywords:
            if kw in corpus:
                tags.append(kw)
        return tags

    def parse(self, raw: Dict[str, Any]) -> Optional[ScrapedJob]:
        try:
            title = raw.get("title", "").strip()
            if not title or len(title) < 3:
                return None

            description = raw.get("description") or ""
            tags = raw.get("tags", []) or []

            salary_min = raw.get("salary_min")
            salary_max = raw.get("salary_max")
            if salary_min is None and salary_max is None:
                salary_text = raw.get("salary_text", "")
                if salary_text:
                    salary_min, salary_max = parse_salary(salary_text)

            seniority = self._infer_seniority(title, description)
            emp_type = self._infer_employment_type(title, description)

            if not tags:
                tags = self._extract_tags(title, description)

            return ScrapedJob(
                title=title,
                company=raw.get("company", "").strip() or "Unknown",
                location=raw.get("location", "").strip() or "Brasil",
                remote=raw.get("remote", False),
                description=truncate(description),
                tags=tags,
                job_url=raw.get("detail_url", ""),
                salary_min=salary_min,
                salary_max=salary_max,
                currency="BRL",
                source=self.source_name(),
                seniority=seniority,
                employment_type=emp_type,
                posted_at=raw.get("posted_at"),
            )
        except Exception as e:
            logger.warning("Failed to parse Google Jobs entry: %s", e)
            return None

    async def run(self) -> int:
        raw_jobs = await self.fetch_raw()
        inserted_count = 0

        for i, raw in enumerate(raw_jobs):
            job = self.parse(raw)
            if job is None:
                continue

            company_id = self._db.get_or_create_company(job.company)
            if company_id is None:
                logger.warning("Skipping '%s': failed to resolve company", job.title)
                continue

            job_id = self._db.upsert_job({
                "p_company_id": company_id,
                "p_title": job.title,
                "p_description": job.description or "",
                "p_location": job.location,
                "p_remote": job.remote,
                "p_seniority": job.seniority,
                "p_employment_type": job.employment_type,
                "p_salary_min": job.salary_min,
                "p_salary_max": job.salary_max,
                "p_currency": job.currency,
                "p_job_url": job.job_url,
                "p_source": self.source_name(),
                "p_posted_at": job.posted_at,
            })

            if job_id:
                slugs = self._skill_extractor.extract(job.tags, job.description or "")
                self._db.attach_skills(job_id, slugs)
                inserted_count += 1
                logger.info("[%d/%d] + %s @ %s", i + 1, len(raw_jobs), job.title, job.company)
            else:
                logger.debug("[%d/%d] ~ %s (skipped)", i + 1, len(raw_jobs), job.title)

        return inserted_count
