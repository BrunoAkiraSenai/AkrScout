import asyncio
import re
import random
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from playwright.async_api import async_playwright, Page, BrowserContext, Browser

from config.settings import (
    INDEED_SEARCH_URL,
    INDEED_SEARCH_QUERIES,
    INDEED_MAX_PAGES,
    INDEED_MAX_JOBS,
    INDEED_DELAY_MIN,
    INDEED_DELAY_MAX,
    INDEED_PAGE_DELAY_MIN,
    INDEED_PAGE_DELAY_MAX,
    REQUEST_TIMEOUT,
    BROWSER_HEADLESS,
)
from parsers.skill_extractor import SkillExtractor
from services.supabase import DatabaseService
from utils.logger import setup_logger
from utils.normalizer import clean_html, parse_salary, truncate

from .base import BaseScraper, ScrapedJob

logger = setup_logger("indeed")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

VIEWPORTS = [
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1920, "height": 1080},
]


class IndeedScraper(BaseScraper):
    def __init__(self, db: DatabaseService):
        self._db = db
        self._skill_extractor = SkillExtractor()
        self._collected: List[Dict[str, Any]] = []

    def source_name(self) -> str:
        return "indeed"

    def _random_delay(self, min_s: float = None, max_s: float = None) -> float:
        min_s = min_s or INDEED_DELAY_MIN
        max_s = max_s or INDEED_DELAY_MAX
        delay = random.uniform(min_s, max_s)
        return delay

    async def _create_browser(self, playwright) -> Browser:
        ua = random.choice(USER_AGENTS)
        browser = await playwright.chromium.launch(
            headless=BROWSER_HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-features=IsolateOrigins,site-per-process",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-web-security",
                "--disable-features=DialMediaRouteProvider",
            ],
        )
        return browser

    async def _create_context(self, browser: Browser) -> BrowserContext:
        ua = random.choice(USER_AGENTS)
        vp = random.choice(VIEWPORTS)
        context = await browser.new_context(
            user_agent=ua,
            viewport=vp,
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            bypass_csp=True,
        )
        await self._apply_stealth(context)
        return context

    async def _apply_stealth(self, context: BrowserContext) -> None:
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['pt-BR', 'pt', 'en-US', 'en'],
            });
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {},
            };
            if (window.navigator.permissions) {
                const orig = window.navigator.permissions.query.bind(window.navigator.permissions);
                window.navigator.permissions.query = (p) => (
                    p.name === 'notifications'
                        ? Promise.resolve({ state: 'denied' })
                        : orig(p)
                );
            }
        """)

    async def _dismiss_cookies(self, page: Page) -> None:
        try:
            selectors = [
                'button[aria-label*="cookie"]',
                'button[aria-label*="Cookie"]',
                "button#onetrust-accept-btn-handler",
                'button:has-text("Aceitar")',
                'button:has-text("Accept")',
                'button:has-text("Permitir")',
                'button:has-text("Aceitar todos")',
                "#cookie-consent button",
                '[data-testid="cookie-banner"] button',
                'button[class*="cookie"]',
                'button[id*="cookie"]',
            ]
            for sel in selectors:
                try:
                    btn = await page.wait_for_selector(sel, timeout=3000)
                    if btn:
                        await btn.click(timeout=2000)
                        await asyncio.sleep(0.5)
                        logger.debug("Dismissed cookie banner")
                        return
                except Exception:
                    continue
        except Exception:
            pass

    async def _search_pages(self, context: BrowserContext) -> None:
        for query in INDEED_SEARCH_QUERIES:
            if len(self._collected) >= INDEED_MAX_JOBS:
                break

            logger.info("Searching Indeed for: %s", query)

            cards = []

            # Strategy 1: curl_cffi JSON API (fastest, no browser)
            if not cards:
                cards = await self._search_api(query)

            # Strategy 2: curl_cffi RSS feed
            if not cards:
                cards = await self._search_rss(query)

            # Strategy 3: Playwright with stealth (browser-based)
            if not cards:
                logger.info("API/RSS failed, trying Playwright browser for '%s'", query)
                for page_num in range(INDEED_MAX_PAGES):
                    if len(self._collected) >= INDEED_MAX_JOBS:
                        break

                    page = await context.new_page()
                    try:
                        params = {"q": query, "limit": 50, "sort": "date"}
                        if page_num > 0:
                            params["start"] = page_num * 50

                        url = f"{INDEED_SEARCH_URL}?{urlencode(params)}"
                        logger.debug("Fetching: %s", url)

                        await page.goto(url, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT)
                        await page.wait_for_load_state("load", timeout=REQUEST_TIMEOUT)

                        await self._dismiss_cookies(page)
                        await asyncio.sleep(2)

                        for _ in range(3):
                            await page.evaluate("window.scrollBy(0, 600)")
                            await asyncio.sleep(self._random_delay(1, 2))

                        await asyncio.sleep(self._random_delay(1, 2))

                        pw_cards = await self._extract_search_cards(page)
                        cards.extend(pw_cards)
                        logger.info("Playwright found %d cards on page %d for '%s'", len(pw_cards), page_num + 1, query)
                    except Exception as e:
                        logger.warning("Playwright page %d failed for '%s': %s", page_num + 1, query, e)
                    finally:
                        await page.close()

                    if page_num < INDEED_MAX_PAGES - 1:
                        await asyncio.sleep(self._random_delay(INDEED_PAGE_DELAY_MIN, INDEED_PAGE_DELAY_MAX))

            for card in cards:
                if len(self._collected) >= INDEED_MAX_JOBS:
                    break
                await self._enrich_job(context, card)
                await asyncio.sleep(self._random_delay())

    async def _extract_search_cards(self, page: Page) -> List[Dict[str, Any]]:
        cards = []
        try:
            page_text = await page.evaluate("document.body.innerText.substring(0, 1000)")
            page_text_lower = page_text.lower()

            blocked = ["captcha", "verify", "robot", "automated", "access denied", "please confirm you are human"]
            for kw in blocked:
                if kw in page_text_lower:
                    logger.warning("Blocking detected on Indeed (keyword: '%s')", kw)
                    body_preview = page_text.replace('\n', ' ')[:300]
                    logger.debug("Blocked page: %s", body_preview)
                    return cards

            no_results = ["no results", "nenhum resultado", "0 resultados", "no jobs found", "no matching jobs"]
            for nr in no_results:
                if nr in page_text_lower:
                    logger.info("Indeed returned no results for this query")
                    return cards

            cards = await page.evaluate("""
                () => {
                    const results = [];
                    const seen = new Set();
                    const links = document.querySelectorAll('a');
                    for (const link of links) {
                        try {
                            const href = link.getAttribute('href') || '';
                            const jkMatch = href.match(/[?&]jk=([a-fA-F0-9]+)/);
                            if (!jkMatch) continue;
                            const jk = jkMatch[1];
                            if (!jk || seen.has(jk)) continue;
                            seen.add(jk);

                            let title = (link.innerText || link.textContent || '').trim();
                            if (!title || title.length < 3) continue;

                            const parent = link.closest('[class*="card"], [class*="result"], [data-testid*="job"], li, .job_seen_beacon, article');
                            let company = '';
                            let location = '';
                            if (parent) {
                                const spans = parent.querySelectorAll('span, div');
                                for (const s of spans) {
                                    const txt = (s.innerText || '').trim();
                                    if (!txt || txt === title) continue;
                                    if (s.closest('a')) continue;
                                    if (!company && txt.length > 1 && txt.length < 80 && !txt.includes('http')) company = txt;
                                    else if (!location && txt.length > 1 && txt.length < 80 && !txt.includes('http')) location = txt;
                                }
                            }

                            results.push({
                                jk: jk,
                                title: title,
                                company: company,
                                location: location,
                                url: 'https://br.indeed.com/viewjob?jk=' + jk,
                            });
                        } catch(e) {}
                    }
                    return results;
                }
            """)

            if not cards:
                logger.warning("No cards via href jk=, trying broader search...")
                cards = await page.evaluate("""
                    () => {
                        const results = [];
                        const seen = new Set();

                        const allElements = document.querySelectorAll('[data-jk]');
                        for (const el of allElements) {
                            try {
                                const jk = el.getAttribute('data-jk');
                                if (!jk || seen.has(jk) || jk.length < 5) continue;
                                seen.add(jk);

                                const title = (el.innerText || el.textContent || '').trim().substring(0, 100);
                                if (!title || title.length < 5) continue;

                                results.push({
                                    jk: jk,
                                    title: title,
                                    company: '',
                                    location: '',
                                    url: 'https://br.indeed.com/viewjob?jk=' + jk,
                                });
                            } catch(e) {}
                        }
                        return results;
                    }
                """)

            if not cards:
                logger.warning("No cards via data-jk, trying href pattern...")
                cards = await page.evaluate("""
                    () => {
                        const results = [];
                        const seen = new Set();
                        const links = document.querySelectorAll('a[href*="viewjob"], a[href*="rc/clk"]');
                        for (const link of links) {
                            try {
                                const href = link.getAttribute('href') || '';
                                const jkMatch = href.match(/jk=([a-fA-F0-9]+)/);
                                if (!jkMatch) continue;
                                const jk = jkMatch[1];
                                if (!jk || seen.has(jk)) continue;
                                seen.add(jk);

                                let title = (link.innerText || link.textContent || '').trim();
                                if (!title || title.length < 3) continue;

                                results.push({
                                    jk: jk,
                                    title: title,
                                    company: '',
                                    location: '',
                                    url: 'https://br.indeed.com/viewjob?jk=' + jk,
                                });
                            } catch(e) {}
                        }
                        return results;
                    }
                """)

            if not cards:
                logger.warning("No cards found via any strategy on Indeed")
                body_sample = page_text.replace('\n', ' ')[:300]
                logger.info("Indeed page content: %s", body_sample)
                html_sample = await page.evaluate("document.body.innerHTML.substring(0, 1500)")
                logger.debug("Indeed HTML sample: %s", html_sample[:500])

        except Exception as e:
            logger.warning("Card extraction error: %s", e)

        return cards

    async def _request_impersonate(self, url: str, accept: str = "text/html") -> Optional[str]:
        try:
            from curl_cffi.requests import AsyncSession
            async with AsyncSession(impersonate="chrome120") as session:
                resp = await session.get(url, timeout=30, headers={"Accept": accept})
                if resp.status_code == 200 and not self._is_cloudflare_body(resp.text[:500]):
                    return resp.text
                logger.debug("Impersonated request blocked (status=%d): %s", resp.status_code, url[:80])
                return None
        except Exception as e:
            logger.debug("Impersonated request failed: %s", e)
            return None

    def _is_cloudflare_body(self, text: str) -> bool:
        lower = text.lower()
        keywords = ["cloudflare", "ray id", "verificação adicional", "checking your browser",
                    "cf-ray", "attention required", "please confirm you are human"]
        return any(kw in lower for kw in keywords)

    async def _search_api(self, query: str) -> List[Dict[str, Any]]:
        import json

        params = {"q": query, "l": "", "start": "0", "limit": "50", "sort": "date"}
        url = f"https://br.indeed.com/jobs/api/v1/search?{urlencode(params)}"
        logger.debug("Indeed API URL: %s", url)

        html = await self._request_impersonate(url, accept="application/json")
        if not html:
            return []

        try:
            data = json.loads(html)
        except json.JSONDecodeError:
            return []

        results = data.get("results", data.get("jobs", data.get("jobData", [])))
        if not results and isinstance(data, list):
            results = data

        cards = []
        for job in results:
            try:
                jk = job.get("jobKey") or job.get("jk")
                if not jk:
                    continue
                title = (job.get("jobTitle") or job.get("title") or "").strip()
                if not title:
                    continue
                cards.append({
                    "jk": jk,
                    "title": title,
                    "company": (job.get("company") or job.get("employer") or {}).get("name") if isinstance(job.get("company"), dict) else (job.get("company") or ""),
                    "location": (job.get("city") or "") + (", " + job.get("state") if job.get("state") else ""),
                    "url": f"https://br.indeed.com/viewjob?jk={jk}",
                    "salary_text": job.get("salary", {}).get("text") if isinstance(job.get("salary"), dict) else job.get("salaryText", ""),
                    "posted_at": job.get("formattedRelativeTime") or job.get("postedDate", ""),
                })
                cards_company = job.get("company") or ""
                if isinstance(job.get("company"), dict):
                    cards_company = job["company"].get("name", "")
                cards[-1]["company"] = cards_company
            except Exception:
                continue

        logger.info("API search found %d jobs for '%s'", len(cards), query)
        return cards

    async def _search_rss(self, query: str) -> List[Dict[str, Any]]:
        import xml.etree.ElementTree as ET

        url = f"https://br.indeed.com/rss?q={query.replace(' ', '+')}"
        logger.debug("RSS fallback URL: %s", url)

        html = await self._request_impersonate(url, accept="application/rss+xml, application/xml, text/xml, */*")
        if not html:
            return []

        try:
            root = ET.fromstring(html.encode())
        except ET.ParseError:
            return []

        cards = []
        for item in root.iter("item"):
            try:
                title_el = item.find("title")
                link_el = item.find("link")
                desc_el = item.find("description")

                title = title_el.text.strip() if title_el is not None and title_el.text else ""
                link = link_el.text.strip() if link_el is not None and link_el.text else ""

                if not title or not link:
                    continue

                jk_match = re.search(r'jk=([a-fA-F0-9]+)', link)
                if not jk_match:
                    continue
                jk = jk_match.group(1)

                desc = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
                company = ""
                location = ""
                if desc:
                    clean = re.sub(r'<[^>]+>', '', desc.replace("<br>", "\n").replace("<br/>", "\n"))
                    for line in clean.split("\n"):
                        line = line.strip()
                        if not line:
                            continue
                        if not company:
                            company = line
                        elif not location:
                            location = line
                            break

                cards.append({
                    "jk": jk,
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": f"https://br.indeed.com/viewjob?jk={jk}",
                    "description": desc,
                })
            except Exception:
                continue

        logger.info("RSS search found %d jobs for '%s'", len(cards), query)
        return cards

    async def _enrich_job(self, context: BrowserContext, card: Dict[str, Any]) -> None:
        detail_page = await context.new_page()
        try:
            jk = card["jk"]
            detail_url = card["url"]

            logger.debug("Fetching detail: %s", detail_url)
            await detail_page.goto(detail_url, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT)
            await asyncio.sleep(self._random_delay(1, 3))

            html = await detail_page.content()
            job_data = await self._parse_detail_page(detail_page, card)
            if job_data:
                self._collected.append(job_data)
                logger.info("Collected: %s @ %s", job_data.get("title", "?"), job_data.get("company", "?"))

        except Exception as e:
            logger.warning("Failed to enrich job %s: %s", card.get("jk", "?"), e)
        finally:
            await detail_page.close()

    async def _parse_detail_page(self, page: Page, card: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            title = card.get("title", "")

            company = ""
            company_selectors = [
                '[data-testid="company-name"]',
                'span[class*="company"]',
                'div[class*="company"]',
                '[data-company-name]',
                'a[data-testid*="company"]',
            ]
            for sel in company_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        company = await el.inner_text()
                        company = company.strip()
                        if company:
                            break
                except Exception:
                    continue

            location = ""
            location_selectors = [
                '[data-testid="job-location"]',
                'div[class*="location"]',
                'span[class*="location"]',
                '[data-testid="jobLocation"]',
            ]
            for sel in location_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        location = await el.inner_text()
                        location = location.strip()
                        if location:
                            break
                except Exception:
                    continue

            remote_text = (title + " " + location + " " + company).lower()
            remote = any(w in remote_text for w in ["remoto", "remote", "home office", "home-office", "100% remoto", "trabalho remoto", "work from home", "wfh", "virtual", "anywhere"])

            salary_text = ""
            salary_selectors = [
                '[data-testid="salary"]',
                'div[class*="salary"]',
                'span[class*="salary"]',
                'div.metadata.salary-snippet-container',
                'div.salary-snippet',
                '#salaryRange',
                '[data-testid*="salary"]',
            ]
            for sel in salary_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        salary_text = await el.inner_text()
                        salary_text = salary_text.strip()
                        if salary_text:
                            break
                except Exception:
                    continue

            salary_min, salary_max = None, None
            if salary_text:
                salary_min, salary_max = parse_salary(salary_text)
                if salary_min is None and salary_max is None:
                    salary_min, salary_max = self._parse_indeed_salary(salary_text)

            description = ""
            desc_selectors = [
                'div[data-testid="jobDescriptionText"]',
                'div.jobsearch-jobDescriptionText',
                'div[id*="jobDescription"]',
                'div[id*="description"]',
                'div[class*="description"]',
                '#jobDescriptionText',
                '[data-testid="job-description"]',
            ]
            for sel in desc_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        description = await el.inner_html()
                        break
                except Exception:
                    continue

            if description:
                description = clean_html(description) or ""
            description = description or ""

            posted_at = ""
            posted_selectors = [
                '[data-testid="job-date"]',
                'span[class*="date"]',
                'div[class*="date"]',
                '[data-testid="postedDate"]',
            ]
            for sel in posted_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        posted_at = await el.inner_text()
                        posted_at = posted_at.strip()
                        if posted_at:
                            break
                except Exception:
                    continue

            posted_parsed = self._parse_indeed_date(posted_at) if posted_at else None

            tags = self._extract_tags(title, description)

            return {
                "title": title,
                "company": company,
                "location": location,
                "remote": remote,
                "description": description,
                "tags": tags,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "salary_text": salary_text,
                "detail_url": card.get("url", ""),
                "posted_at": posted_parsed,
            }

        except Exception as e:
            logger.warning("Failed to parse detail page: %s", e)
            return None

    def _parse_indeed_salary(self, text: str) -> tuple:
        text_clean = text.replace(".", "").replace(",", ".").strip()
        ranges = re.findall(r"R\$\s*(\d+[\d.]*(?:,\d+)?)", text_clean)
        if ranges:
            values = []
            for r in ranges:
                val = float(r.replace(",", "."))
                values.append(val)
            if len(values) >= 2:
                return min(values), max(values)
            if len(values) == 1:
                return values[0], None

        numbers = re.findall(r"(\d+(?:\.\d+)?(?:,\d+)?)", text_clean)
        parsed = []
        for n in numbers:
            try:
                val = float(n.replace(",", ""))
                if val > 100:
                    parsed.append(val)
            except ValueError:
                continue

        if len(parsed) >= 2:
            return min(parsed), max(parsed)
        if len(parsed) == 1:
            return parsed[0], None
        return None, None

    def _parse_indeed_date(self, text: str) -> Optional[str]:
        text_lower = text.lower().strip()
        if "hoje" in text_lower or "agora" in text_lower or "momentos" in text_lower:
            from datetime import datetime, timezone
            return datetime.now(timezone.utc).isoformat()

        import re as _re
        match = _re.search(r"há\s*(\d+)\s*(minuto|hora|dia|semana|mês|mês|ano)", text_lower)
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            if "minuto" in unit:
                dt = now - timedelta(minutes=amount)
            elif "hora" in unit:
                dt = now - timedelta(hours=amount)
            elif "dia" in unit:
                dt = now - timedelta(days=amount)
            elif "semana" in unit:
                dt = now - timedelta(weeks=amount)
            elif "mês" in unit or "mes" in unit:
                dt = now - timedelta(days=amount * 30)
            elif "ano" in unit:
                dt = now - timedelta(days=amount * 365)
            else:
                dt = now
            return dt.isoformat()

        match = _re.search(r"(\d+)\s*(minute|hour|day|week|month|year)", text_lower)
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            if "minute" in unit:
                dt = now - timedelta(minutes=amount)
            elif "hour" in unit:
                dt = now - timedelta(hours=amount)
            elif "day" in unit:
                dt = now - timedelta(days=amount)
            elif "week" in unit:
                dt = now - timedelta(weeks=amount)
            elif "month" in unit:
                dt = now - timedelta(days=amount * 30)
            elif "year" in unit:
                dt = now - timedelta(days=amount * 365)
            else:
                dt = now
            return dt.isoformat()

        return None

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

    async def fetch_raw(self) -> List[Dict[str, Any]]:
        self._collected = []
        logger.info("Indeed scraping started (max %d jobs, %d queries)", INDEED_MAX_JOBS, len(INDEED_SEARCH_QUERIES))

        async with async_playwright() as pw:
            browser = await self._create_browser(pw)
            try:
                context = await self._create_context(browser)
                try:
                    await self._search_pages(context)
                finally:
                    await context.close()
            finally:
                await browser.close()

        logger.info("Indeed collected %d raw entries", len(self._collected))
        return self._collected

    def _normalize_seniority(self, text: str) -> Optional[str]:
        if not text:
            return None
        mapping = {
            "junior": "junior",
            "jr": "junior",
            "júnior": "junior",
            "pleno": "mid",
            "mid": "mid",
            "senior": "senior",
            "sr": "senior",
            "sênior": "senior",
            "sénior": "senior",
            "estágio": "intern",
            "estagiario": "intern",
            "estagiário": "intern",
            "trainee": "intern",
        }
        text_lower = text.lower().strip()
        for key, val in mapping.items():
            if key in text_lower:
                return val
        return None

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
            logger.warning("Failed to parse Indeed job: %s", e)
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
                logger.warning("Skipping job '%s': failed to resolve company", job.title)
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
                logger.info(
                    "[%d/%d] + %s @ %s",
                    i + 1,
                    len(raw_jobs),
                    job.title,
                    job.company,
                )
            else:
                logger.debug(
                    "[%d/%d] ~ %s (skipped)", i + 1, len(raw_jobs), job.title
                )

        return inserted_count
