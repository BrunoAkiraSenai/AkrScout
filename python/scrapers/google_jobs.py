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
        # Google Jobs is JavaScript-rendered — curl_cffi cannot extract job data.
        # Return empty to trigger the Playwright fallback immediately.
        logger.debug("Skipping curl_cffi for '%s' (JS-rendered, Playwright will handle)", query)
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

    def _parse_xhr_jobs(self, xhr_responses: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        cards = []
        seen = set()

        for xhr in xhr_responses:
            body = xhr.get("body", "")
            if not body:
                continue

            # Try direct JSON parse
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                pass

            # Try to find JSON inside async response (Google wraps in `)]}'\n`)
            for prefix in [")]}'\n", ")]}'\n"]:
                if body.startswith(prefix):
                    try:
                        data = json.loads(body[len(prefix):])
                    except (json.JSONDecodeError, IndexError):
                        pass

            if not data:
                continue

            # Navigate to the job array in Google's response structure
            items = data
            if isinstance(data, dict):
                for key in ["jobs", "results", "items", "data", "job_results"]:
                    if key in data and isinstance(data[key], list):
                        items = data[key]
                        break

            if not isinstance(items, list):
                items = [items]

            for item in items:
                if not isinstance(item, dict):
                    continue
                title = item.get("jobTitle") or item.get("title") or item.get("name") or ""
                title = title.strip()
                if not title or len(title) < 4 or title in seen:
                    continue
                seen.add(title)

                company = ""
                org = item.get("hiringOrganization") or item.get("company") or item.get("employer") or {}
                if isinstance(org, dict):
                    company = org.get("name", "") or org.get("legalName", "")
                elif isinstance(org, str):
                    company = org

                location = ""
                loc = item.get("jobLocation") or item.get("location") or {}
                if isinstance(loc, dict):
                    loc_name = loc.get("name", "")
                    loc_addr = loc.get("address", "")
                    location = loc_name or loc_addr
                elif isinstance(loc, str):
                    location = loc

                desc = item.get("description") or item.get("snippet") or ""
                if isinstance(desc, dict):
                    desc = desc.get("value", "")

                salary_min, salary_max = None, None
                salary = item.get("baseSalary") or item.get("salary") or {}
                if isinstance(salary, dict):
                    value = salary.get("value") or {}
                    if isinstance(value, dict):
                        salary_min = value.get("minValue") or value.get("min")
                        salary_max = value.get("maxValue") or value.get("max")

                posted_at = item.get("datePosted") or item.get("postedDate") or item.get("publishedDate") or ""
                job_url = item.get("url") or item.get("link") or item.get("jobUrl") or ""

                remote = any(w in title.lower() for w in ["remoto", "remote", "home office"]) or \
                         any(w in (desc or "").lower() for w in ["remoto", "remote", "home office"])

                cards.append({
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
                    "direct_apply": False,
                })

        if cards:
            logger.info("XHR parser extracted %d jobs from %d responses for '%s'",
                        len(cards), len(xhr_responses), query)
        return cards

    async def _search_with_playwright(self, query: str) -> List[Dict[str, Any]]:
        from playwright.async_api import async_playwright
        from pathlib import Path

        debug_dir = Path("logs") / "google-jobs-debug"
        debug_dir.mkdir(parents=True, exist_ok=True)

        params = {
            "q": f"{query} brasil vaga",
            "udm": "8",
            "gl": GOOGLE_JOBS_COUNTRY,
            "hl": GOOGLE_JOBS_LANG,
        }
        url = f"https://www.google.com/search?{urlencode(params)}"
        logger.info("Playwright Google Jobs URL: %s", url)
        safe_query = query.replace(" ", "_")

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
                logger.info("PW browser: system Chrome")
            except Exception:
                launch_opts.pop("channel", None)
                browser = await pw.chromium.launch(**launch_opts)
                logger.info("PW browser: bundled Chromium")

            try:
                context = await browser.new_context(
                    user_agent=random.choice(USER_AGENTS),
                    viewport={"width": 1920, "height": 1080},
                    locale="pt-BR",
                    timezone_id="America/Sao_Paulo",
                )
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                    Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
                    Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR','pt','en-US'] });
                    window.chrome = { runtime: {}, loadTimes: () => {}, csi: () => {}, app: {} };
                """)

                page = await context.new_page()

                # XHR route interception — capture Google Jobs API responses
                xhr_jobs: List[Dict] = []
                async def on_response(response):
                    try:
                        rurl = response.url
                        if 'async/job' in rurl or 'job_status' in rurl or 'job_search' in rurl:
                            body = await response.text()
                            if body and len(body) > 100:
                                logger.info("PW: XHR captured %s (%d bytes)", rurl, len(body))
                                (debug_dir / f"xhr_{safe_query}_{len(xhr_jobs)}.json").write_text(body, encoding="utf-8")
                                xhr_jobs.append({"url": rurl, "body": body})
                    except Exception:
                        pass
                page.on("response", lambda resp: asyncio.ensure_future(on_response(resp)))

                logger.info("PW: navigating...")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                current_url = page.url
                logger.info("PW: final URL: %s", current_url)
                await page.screenshot(path=str(debug_dir / f"01_after_load_{safe_query}.png"))
                logger.info("PW: page loaded, title='%s'", await page.title())

                html_after_load = await page.content()
                (debug_dir / f"html_after_load_{safe_query}.html").write_text(html_after_load, encoding="utf-8")
                logger.info("PW: HTML after load: %d bytes", len(html_after_load))

                logger.info("PW: waiting for network idle...")
                try:
                    await page.wait_for_load_state("networkidle", timeout=30000)
                except Exception as e:
                    logger.warning("PW: networkidle timeout: %s", e)
                await page.screenshot(path=str(debug_dir / f"02_after_networkidle_{safe_query}.png"))

                logger.info("PW: waiting for job results rendering...")
                await asyncio.sleep(5)

                # Try parsing XHR data first (cleanest approach)
                cards = self._parse_xhr_jobs(xhr_jobs, query)
                if cards:
                    logger.info("PW: XHR extraction found %d jobs for '%s'", len(cards), query)
                    await page.screenshot(path=str(debug_dir / f"05_final_{safe_query}.png"))
                    for c in cards[:5]:
                        logger.info("PW: sample XHR card: '%s' @ %s [%s]", c["title"], c["company"], c["location"])
                    return cards

                logger.info("PW: scanning DOM structure...")
                dom_scan = await page.evaluate("""
                    () => {
                        const results = {};
                        const all = document.querySelectorAll('*');
                        for (const el of all) {
                            const tag = el.tagName.toLowerCase();
                            const cls = el.className || '';
                            const hasDataDocid = el.hasAttribute('data-docid');
                            if (!results[tag]) results[tag] = { count: 0, classes: new Set(), dataDocid: false };
                            results[tag].count++;
                            if (cls && typeof cls === 'string') {
                                cls.split(/\\s+/).forEach(c => { if (c) results[tag].classes.add(c); });
                            }
                            if (hasDataDocid) results[tag].dataDocid = true;
                        }
                        const summary = {};
                        for (const [tag, info] of Object.entries(results)) {
                            summary[tag] = {
                                count: info.count,
                                hasDataDocid: info.dataDocid,
                                classes: Array.from(info.classes).slice(0, 10),
                            };
                        }
                        return summary;
                    }
                """)
                for tag, info in sorted(dom_scan.items(), key=lambda x: -x[1]["count"]):
                    if info["count"] > 1 or info["hasDataDocid"] or info["classes"]:
                        logger.info("PW: DOM <%s> count=%d hasDocid=%s classes=%s",
                                    tag, info["count"], info["hasDataDocid"], info["classes"][:5])

                key_selectors = [
                    "div[role='feed']", "[role='list']", "[data-docid]",
                    "gws-plugins-horizon-jobs", "[class*='gws-plugins']",
                    "div[jscontroller]", "h3", "a[href*='/jobs']",
                ]
                for sel in key_selectors:
                    try:
                        count = await page.locator(sel).count()
                        if count > 0:
                            logger.info("PW: selector '%s' = %d elements", sel, count)
                    except Exception:
                        pass

                await page.screenshot(path=str(debug_dir / f"03_before_scroll_{safe_query}.png"))
                for i in range(5):
                    await page.evaluate("(y) => window.scrollBy(0, y)", 400 + i * 200)
                    await asyncio.sleep(1.5)
                await asyncio.sleep(3)
                await page.screenshot(path=str(debug_dir / f"04_after_scroll_{safe_query}.png"))

                # Container analysis
                container_info = await page.evaluate("""
                    () => {
                        const info = [];
                        document.querySelectorAll('[role="feed"]').forEach((el, i) => {
                            const preview = el.innerHTML.substring(0, 500).replace(/<[^>]+>/g,' ').replace(/\\s+/g,' ').trim();
                            info.push({ type: 'role-feed', index: i, children: el.children.length, preview: preview.substring(0, 300) });
                        });
                        document.querySelectorAll('[role="list"]').forEach((el, i) => {
                            const preview = el.innerHTML.substring(0, 300).replace(/<[^>]+>/g,' ').replace(/\\s+/g,' ').trim();
                            info.push({ type: 'role-list', index: i, children: el.children.length, preview: preview.substring(0, 200) });
                        });
                        document.querySelectorAll('#center_col, [role="main"], #main').forEach((el, i) => {
                            const preview = el.innerHTML.substring(0, 300).replace(/<[^>]+>/g,' ').replace(/\\s+/g,' ').trim();
                            info.push({ type: 'main', index: i, children: el.children.length, preview: preview.substring(0, 200) });
                        });
                        return info;
                    }
                """)
                for c in container_info:
                    logger.info("PW: container %s [%d] children=%d preview=%s",
                                c["type"], c["index"], c["children"], c["preview"][:150])

                ui_keywords = ["compartilhar", "facebook", "copiar link", "ferramentas",
                               "anúncio", "anuncio", "seguir", "vagas salvas", "empregos",
                               "clique para copiar", "twitter", "linkedin", "whatsapp",
                               "denunciar", "reportar", "candidatar", "candidate-se"]

                cards = await page.evaluate("""
                    () => {
                        const BAD_KEYWORDS = ["compartilhar","facebook","copiar link","ferramentas",
                                               "anúncio","anuncio","seguir","vagas salvas","empregos",
                                               "clique","twitter","linkedin","whatsapp","denunciar",
                                               "reportar","candidatar","candidate","salvar",
                                               "videos","notícias","shopping","modo ia",
                                               "finanças","imagens","maps",
                                               "todas","livros","voos","finance"];

                        function extractFromContainer(container) {
                            const cards = [];
                            const seen = new Set();
                            const items = container.children;
                            for (const item of items) {
                                try {
                                    const titleEl = item.querySelector('h3, h2, [class*="title"], a[href*="http"]:not([class*="nav"])');
                                    if (!titleEl) continue;
                                    const title = (titleEl.innerText || titleEl.textContent || '').trim();
                                    if (!title || title.length < 5 || seen.has(title)) continue;
                                    const ltitle = title.toLowerCase();
                                    if (BAD_KEYWORDS.some(k => ltitle.includes(k))) continue;
                                    seen.add(title);

                                    const link = item.querySelector('a[href*="http"]');
                                    const url = link ? link.href : '';
                                    if (!url) continue;

                                    const allText = item.innerText || '';
                                    const lines = allText.split('\\n').map(l => l.trim()).filter(l => l && l !== title);
                                    let company = '';
                                    let location = '';
                                    for (const line of lines) {
                                        if (!company && line.length > 1 && line.length < 60) company = line;
                                        else if (!location && line.length > 1 && line.length < 80) location = line;
                                    }

                                    cards.push({ title, company, location, salaryText: '', dateText: '', url });
                                } catch(e) {}
                            }
                            return cards;
                        }

                        // Strategy 1: role="feed" — Google Jobs panel
                        let results = [];
                        const feeds = document.querySelectorAll('[role="feed"]');
                        for (const feed of feeds) {
                            const found = extractFromContainer(feed);
                            if (found.length > 0) { results = found; break; }
                        }

                        // Strategy 2: data-docid parents (Google card identifiers)
                        if (!results.length) {
                            const docidParents = new Set();
                            document.querySelectorAll('[data-docid]').forEach(el => docidParents.add(el.parentElement));
                            for (const parent of docidParents) {
                                if (parent && parent.children.length >= 2) {
                                    const found = extractFromContainer(parent);
                                    if (found.length > 0) { results = found; break; }
                                }
                            }
                        }

                        // Strategy 3: gws-plugins-horizon-jobs
                        if (!results.length) {
                            const gwsEls = document.querySelectorAll('gws-plugins-horizon-jobs, [class*="gws-plugins-horizon-jobs"]');
                            for (const g of gwsEls) {
                                const found = extractFromContainer(g);
                                if (found.length > 0) { results = found; break; }
                            }
                        }

                        // Strategy 4: role="list" in main content
                        if (!results.length) {
                            const centerAreas = document.querySelectorAll('#center_col, #main, [role="main"]');
                            for (const area of centerAreas) {
                                const lists = area.querySelectorAll('[role="list"], [role="listbox"]');
                                for (const list of lists) {
                                    const found = extractFromContainer(list);
                                    if (found.length > 0) { results = found; break; }
                                }
                                if (results.length) break;
                            }
                        }

                        // Strategy 5: score divs by job-link count
                        if (!results.length) {
                            const allDivs = document.querySelectorAll('div, ul, ol');
                            const scored = [];
                            for (const el of allDivs) {
                                const children = Array.from(el.children).filter(c => c.tagName === 'DIV' || c.tagName === 'LI');
                                if (children.length < 3 || children.length > 80) continue;
                                const jobLinks = children.filter(c => c.querySelector('a[href*="job"], a[href*="vaga"]'));
                                if (jobLinks.length >= 2) scored.push({ el, score: jobLinks.length, total: children.length });
                            }
                            scored.sort((a, b) => b.score - a.score);
                            for (const s of scored.slice(0, 5)) {
                                const text = (s.el.innerText || '').toLowerCase();
                                const indicators = ['desenvolvedor','analista','engenheiro','salário','empresa','remoto','são paulo'];
                                if (indicators.some(k => text.includes(k))) {
                                    const found = extractFromContainer(s.el);
                                    if (found.length > 0) { results = found; break; }
                                }
                            }
                        }

                        return results;
                    }
                """)

                logger.info("PW: DOM extraction found %d cards", len(cards))

                if not cards:
                    logger.info("PW: DOM extraction 0, trying structured data in scripts...")
                    cards = await page.evaluate("""
                        () => {
                            const results = [];
                            const seen = new Set();
                            const scripts = document.querySelectorAll('script:not([src])');
                            for (const s of scripts) {
                                const text = s.textContent || '';
                                if (!text.includes('jobTitle') && !text.includes('"title"') && !text.includes('hiringOrganization')) continue;
                                try {
                                    const idx = text.indexOf('[');
                                    if (idx === -1) continue;
                                    const sliced = text.slice(idx, idx + 50000);
                                    const end = sliced.lastIndexOf(']');
                                    if (end === -1) continue;
                                    const raw = sliced.slice(0, end + 1);
                                    const arr = JSON.parse(raw);
                                    if (!Array.isArray(arr)) continue;
                                    for (const item of arr) {
                                        if (!item || typeof item !== 'object') continue;
                                        const title = (item.jobTitle || item.title || item.name || '').trim();
                                        if (!title || title.length < 4 || seen.has(title)) continue;
                                        seen.add(title);
                                        const company = (item.company || item.employer || item.hiringOrganization || {}).name || item.company || '';
                                        const loc = (item.location || item.jobLocation || '').name || item.location || item.city || '';
                                        const url = item.url || item.link || item.jobUrl || '';
                                        results.push({ title, company, location: loc, salaryText: '', dateText: '', url });
                                    }
                                } catch(e) {}
                            }
                            return results;
                        }
                    """)
                    if cards:
                        logger.info("PW: script data found %d jobs", len(cards))

                if not cards:
                    logger.info("PW: script data 0, trying link-based extraction...")
                    cards = await page.evaluate("""
                        () => {
                            const results = [];
                            const seen = new Set();
                            const links = document.querySelectorAll('a[href*="/jobs"], a[href*="viewjob"], a[href*="career"], a[href*="vaga"]');
                            for (const a of links) {
                                const title = (a.innerText || a.textContent || '').trim();
                                if (!title || title.length < 5 || seen.has(title)) continue;
                                seen.add(title);
                                const card = a.closest('div, li, article') || a.parentElement;
                                const text = card ? card.innerText : title;
                                const lines = text.split('\\n').map(l => l.trim()).filter(l => l && l !== title);
                                const company = lines.find(l => l.length > 1 && l.length < 60) || '';
                                const location = lines.find(l => l !== company && l.length > 1 && l.length < 80) || '';
                                results.push({ title, company, location, salaryText: '', dateText: '', url: a.href || '' });
                            }
                            return results;
                        }
                    """)
                    if cards:
                        logger.info("PW: link extraction found %d jobs", len(cards))

                # Final UI filter
                filtered = []
                for card in cards:
                    title_lower = card.get("title", "").lower()
                    if any(kw in title_lower for kw in ui_keywords):
                        logger.debug("PW: filtered UI: '%s'", card.get("title"))
                        continue
                    if len(card.get("title", "")) < 4:
                        continue
                    if not card.get("url") and not card.get("company"):
                        continue
                    card["remote"] = any(w in title_lower for w in ["remoto", "remote", "home office", "home-office"])
                    filtered.append(card)
                cards = filtered

                logger.info("PW: %d valid cards after UI filter", len(cards))

                await page.screenshot(path=str(debug_dir / f"05_final_{safe_query}.png"))

                if not cards:
                    body_text = await page.evaluate("document.body.innerText.substring(0, 4000)")
                    logger.info("PW: page body: %s",
                                body_text[:600].replace('\\n', ' ').replace('\\u00a0', ' '))
                else:
                    for c in cards[:5]:
                        logger.info("PW: sample card: '%s' @ %s [%s] url=%s",
                                    c["title"], c["company"], c["location"], c["url"][:80])

                return cards
            finally:
                await browser.close()

    async def fetch_raw(self) -> List[Dict[str, Any]]:
        self._collected = []
        logger.info("Google Jobs scraping started (%d queries — Playwright only, JS-rendered)", len(GOOGLE_JOBS_QUERIES))

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
