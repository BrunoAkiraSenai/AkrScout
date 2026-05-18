import asyncio
import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx

from config.settings import (
    PROGRAMATHOR_CONCURRENCY,
    PROGRAMATHOR_LISTING_URL,
    PROGRAMATHOR_MAX_PAGES,
    REQUEST_TIMEOUT,
)
from parsers.html_parser import parse_html
from parsers.skill_extractor import SkillExtractor
from services.supabase import DatabaseService
from utils.logger import setup_logger
from utils.normalizer import clean_html, parse_date, parse_salary, truncate

from .base import BaseScraper, ScrapedJob

logger = setup_logger("programathor")

BASE_URL = "https://programathor.com.br"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


class ProgramathorScraper(BaseScraper):
    def __init__(self, db: DatabaseService):
        self._db = db
        self._skill_extractor = SkillExtractor()

    def source_name(self) -> str:
        return "programathor"

    def _parse_listing_page(self, html: str) -> List[Dict[str, Any]]:
        soup = parse_html(html)
        cards = soup.select('a[href*="/jobs/"]')
        page_jobs = []

        for a in cards:
            job_path = a.get("href", "")
            if not job_path:
                continue

            if "/page/" in job_path or "contract_type=" in job_path:
                continue

            h3 = a.find("h3")
            if not h3:
                continue

            title = h3.get_text(strip=True)
            if not title or len(title) < 3:
                continue
            title = self._clean_title(title)
            detail_url = urljoin(BASE_URL, job_path)

            company = ""
            location = ""
            salary_text = ""
            seniority = ""
            emp_type = ""
            tags = []
            remote = False

            cell = a.find("div", class_="cell-list-content")
            if cell:
                icon_div = cell.find("div", class_="cell-list-content-icon")
                if icon_div:
                    for span in icon_div.find_all("span"):
                        text = span.get_text(strip=True)
                        i = span.find("i")
                        if i:
                            iclass = " ".join(i.get("class", []))
                            if "fa-briefcase" in iclass:
                                company = text
                            elif "fa-map-marker" in iclass:
                                location = text
                            elif "fa-chart-bar" in iclass:
                                seniority = text
                            elif "fa-file-alt" in iclass:
                                emp_type = text
                        elif "R$" in text:
                            salary_text = text
                for tdiv in cell.find_all("div"):
                    cls = tdiv.get("class", [])
                    if "tag-list" in cls:
                        for tag in tdiv.find_all("span", class_="tag"):
                            tags.append(tag.get_text(strip=True))

            if not company:
                all_text = a.get_text(strip=True)
                parts = [p.strip() for p in all_text.split(title) if p.strip()]
                if parts:
                    raw = parts[0]
                    import re as _re
                    match = _re.search(r'^(.*?)(?:Remoto|Presencial|Híbrido|Hibrido|São Paulo|Belo Horizonte|Rio de Janeiro|Salvador|Brasília|Curitiba|Porto Alegre|Fortaleza|Recife|Florianópolis|Vitória)', raw)
                    if match:
                        company = match.group(1).strip()
                    else:
                        company = raw[:60].strip()

            if not location:
                loc_match = _re.search(r'(Remoto|Presencial|Híbrido|Hibrido)\s*[-–—]?\s*([A-Za-zÀ-ü\s]+)', a.get_text(strip=True))
                if loc_match:
                    location = loc_match.group(0).strip()

            remote = "remoto" in location.lower() or "remoto" in title.lower()

            page_jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "remote": remote,
                "salary_text": salary_text,
                "seniority": self._normalize_seniority(seniority),
                "employment_type": self._normalize_employment_type(emp_type),
                "tags": tags,
                "detail_url": detail_url,
            })

        return page_jobs

    def _parse_detail_page(self, html: str, job: Dict[str, Any]) -> Dict[str, Any]:
        soup = parse_html(html)
        ld = self._extract_job_posting_jsonld(soup)
        if ld:
            desc = ld.get("description", "")
            if desc:
                job["description"] = clean_html(desc) or ""

            posted = ld.get("datePosted")
            if posted:
                job["posted_at"] = parse_date(posted)

            base_salary = ld.get("baseSalary")
            if base_salary and isinstance(base_salary, dict):
                try:
                    value_info = base_salary.get("value", {})
                    if isinstance(value_info, dict):
                        val = value_info.get("value")
                        if val is not None:
                            job["salary_min"] = float(val)
                            job["salary_max"] = float(val)
                            job["currency"] = base_salary.get("currency", "BRL")
                except (ValueError, TypeError):
                    pass

        if not job.get("description"):
            desc_div = soup.find(
                "div",
                class_=lambda c: c and "description" in " ".join(c) if c else False,
            )
            if desc_div:
                job["description"] = clean_html(desc_div.get_text(strip=True)) or ""

        return job

    async def fetch_raw(self) -> List[Dict[str, Any]]:
        jobs_data = []

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT / 1000) as client:
            for page in range(1, PROGRAMATHOR_MAX_PAGES + 1):
                url = f"{PROGRAMATHOR_LISTING_URL}?page={page}"
                logger.info("Fetching listing page %d...", page)

                try:
                    resp = await client.get(url, headers=HEADERS)
                    resp.raise_for_status()
                except Exception as e:
                    logger.warning("Failed to fetch page %d: %s", page, e)
                    break

                page_jobs = self._parse_listing_page(resp.text)
                if not page_jobs:
                    logger.info("No more jobs found, stopping.")
                    break

                jobs_data.extend(page_jobs)
                logger.info("Found %d jobs on page %d", len(page_jobs), page)

        logger.info("Total raw job entries from listing: %d", len(jobs_data))

        if not jobs_data:
            return jobs_data

        sem = asyncio.Semaphore(PROGRAMATHOR_CONCURRENCY)

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT / 1000) as client:
            async def fetch_one(job: Dict[str, Any]) -> Dict[str, Any]:
                async with sem:
                    detail_url = job.get("detail_url", "")
                    if not detail_url:
                        return job
                    try:
                        resp = await client.get(detail_url, headers=HEADERS)
                        resp.raise_for_status()
                        return self._parse_detail_page(resp.text, job)
                    except Exception as e:
                        logger.warning(
                            "Failed to fetch detail %s: %s", detail_url, e
                        )
                        return job

            tasks = [fetch_one(job) for job in jobs_data]
            results = await asyncio.gather(*tasks)

        logger.info("Enriched %d jobs with detail data", len(results))
        return results

    def _extract_job_posting_jsonld(self, soup) -> Optional[Dict]:
        scripts = soup.find_all("script", type="application/ld+json")
        for s in scripts:
            raw = s.string
            if not raw:
                continue
            clean = re.sub(r"[\x00-\x1f\x7f]", "", raw)
            try:
                data = json.loads(clean)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and data.get("@type") == "JobPosting":
                return data
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        return item
        return None

    def _is_expired(self, h3) -> bool:
        vencida = h3.find(
            "span",
            class_=lambda c: c and "color-red" in " ".join(c) if c else False,
        )
        return bool(vencida and "vencida" in vencida.get_text(strip=True).lower())

    def _extract_title(self, h3) -> str:
        texts = []
        for child in h3.children:
            if hasattr(child, "name") and child.name:
                cls = " ".join(child.get("class", []))
                if "badge" in cls or "color-red" in cls or "presential-only" in cls:
                    continue
                texts.append(child.get_text(strip=True))
            elif isinstance(child, str):
                t = child.strip()
                if t:
                    texts.append(t)
        title = " ".join(texts)
        title = self._clean_title(title)
        return title

    def _clean_title(self, title: str) -> str:
        title = re.sub(
            r"^[📍📌🛑]*\s*(PRESENCIAL\s*-\s*SOMENTE\s*PARA\s*CANDIDATOS\s*NO\s*LOCAL\s*)?",
            "",
            title,
            flags=re.IGNORECASE,
        ).strip()
        title = re.sub(r"^Vencida\s*", "", title, flags=re.IGNORECASE).strip()
        return title

    def _normalize_seniority(self, text: str) -> Optional[str]:
        mapping = {
            "junior": "junior",
            "jr": "junior",
            "pleno": "mid",
            "senior": "senior",
            "sênior": "senior",
            "estágio": "intern",
            "trainee": "intern",
        }
        text_lower = text.lower().strip()
        for key, val in mapping.items():
            if key in text_lower:
                return val
        return None

    def _normalize_employment_type(self, text: str) -> Optional[str]:
        mapping = {
            "clt": "full_time",
            "pj": "contract",
            "estágio": "internship",
            "temporary": "contract",
            "freelance": "contract",
        }
        text_lower = text.lower().strip()
        for key, val in mapping.items():
            if key in text_lower:
                return val
        return None

    def parse(self, raw: Dict[str, Any]) -> Optional[ScrapedJob]:
        try:
            title = raw.get("title", "").strip()
            if not title:
                return None

            description = raw.get("description") or ""
            tags = raw.get("tags", []) or []

            salary_min = raw.get("salary_min")
            salary_max = raw.get("salary_max")

            if salary_min is None and salary_max is None:
                salary_text = raw.get("salary_text", "")
                if salary_text:
                    salary_min, salary_max = parse_salary(salary_text)

            return ScrapedJob(
                title=title,
                company=raw.get("company", "").strip() or "Unknown",
                location=raw.get("location", "").strip() or "Remote",
                remote=raw.get("remote", True),
                description=truncate(description),
                tags=tags,
                job_url=raw.get("detail_url", ""),
                salary_min=salary_min,
                salary_max=salary_max,
                currency=raw.get("currency", "BRL"),
                source=self.source_name(),
                seniority=raw.get("seniority"),
                employment_type=raw.get("employment_type"),
                posted_at=raw.get("posted_at"),
            )
        except Exception as e:
            logger.warning("Failed to parse job entry: %s", e)
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
                logger.warning(
                    "Skipping job '%s': failed to resolve company", job.title
                )
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
                slugs = self._skill_extractor.extract(
                    job.tags, job.description or ""
                )
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
