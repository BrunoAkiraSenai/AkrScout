import re
from typing import Any, Dict, List, Optional

from playwright.async_api import async_playwright

from config.settings import REMOTEOK_API_URL, REQUEST_TIMEOUT
from parsers.html_parser import parse_html, extract_json_from_script
from parsers.skill_extractor import SkillExtractor
from services.supabase import DatabaseService
from utils.logger import setup_logger
from utils.normalizer import (
    clean_html,
    parse_date,
    parse_salary,
    truncate,
)

from .base import BaseScraper, ScrapedJob

logger = setup_logger("remoteok")


class RemoteOKScraper(BaseScraper):
    def __init__(self, db: DatabaseService):
        self._db = db
        self._skill_extractor = SkillExtractor()

    def source_name(self) -> str:
        return "remoteok"

    async def fetch_raw(self) -> List[Dict[str, Any]]:
        logger.info("Fetching jobs from RemoteOK API...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page = await ctx.new_page()

            response = await page.goto(REMOTEOK_API_URL, timeout=REQUEST_TIMEOUT)
            raw = await response.json()

            await browser.close()

        if isinstance(raw, list) and len(raw) > 0 and "slug" not in raw[0]:
            raw = raw[1:]

        logger.info("Fetched %d raw job entries", len(raw))
        return raw

    def parse(self, raw: Dict[str, Any]) -> Optional[ScrapedJob]:
        try:
            title = raw.get("position", "").strip()
            if not title:
                return None

            description = clean_html(raw.get("description", "")) or ""
            tags = raw.get("tags", []) or []

            salary_min, salary_max = parse_salary(raw.get("salary"))

            slug = raw.get("slug", "")
            base_url = "https://remoteok.com/remote-jobs"
            job_url = raw.get("url") or f"{base_url}/{slug}" if slug else ""

            posted = parse_date(raw.get("date"))

            return ScrapedJob(
                title=title,
                company=raw.get("company", "").strip() or "Unknown",
                location=raw.get("location", "").strip() or "Remote",
                remote=True,
                description=truncate(description),
                tags=tags,
                job_url=job_url,
                salary_min=salary_min,
                salary_max=salary_max,
                currency="USD",
                source=self.source_name(),
                seniority=self._infer_seniority(title, description),
                employment_type=self._infer_employment_type(title, description),
                posted_at=posted,
            )
        except Exception as e:
            logger.warning("Failed to parse job entry: %s", e)
            return None

    def _infer_seniority(self, title: str, description: str) -> Optional[str]:
        text = (title + " " + description).lower()
        if any(w in text for w in ["junior", "jr", "entry", "trainee", "graduate"]):
            return "junior"
        if any(w in text for w in ["senior", "sr", "staff", "principal", "lead"]):
            return "senior"
        if any(w in text for w in ["mid", "intermediate", "mid-level"]):
            return "mid"
        return None

    def _infer_employment_type(self, title: str, description: str) -> Optional[str]:
        text = (title + " " + description).lower()
        if any(w in text for w in ["part time", "part-time", "parttime"]):
            return "part_time"
        if any(w in text for w in ["contract", "freelance", "temporary", "temp"]):
            return "contract"
        if any(w in text for w in ["intern", "internship"]):
            return "internship"
        return "full_time"

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
                logger.info("[%d/%d] + %s @ %s", i + 1, len(raw_jobs), job.title, job.company)
            else:
                logger.debug("[%d/%d] ~ %s (skipped)", i + 1, len(raw_jobs), job.title)

        return inserted_count
