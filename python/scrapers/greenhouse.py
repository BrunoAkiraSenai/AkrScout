import asyncio
import random
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx

from config.settings import (
    GREENHOUSE_BOARDS,
    GREENHOUSE_CONCURRENCY,
    GREENHOUSE_DELAY_MAX,
    GREENHOUSE_DELAY_MIN,
    GREENHOUSE_MAX_JOBS,
    REQUEST_TIMEOUT,
)
from parsers.skill_extractor import SkillExtractor
from services.supabase import DatabaseService
from utils.logger import setup_logger
from utils.normalizer import clean_html, parse_date, parse_salary, truncate

from .base import BaseScraper, ScrapedJob

logger = setup_logger("greenhouse")

API_BASE = "https://boards-api.greenhouse.io/v1/boards"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


class GreenhouseScraper(BaseScraper):
    def __init__(self, db: DatabaseService):
        self._db = db
        self._skill_extractor = SkillExtractor()
        self._collected: List[Dict[str, Any]] = []

    def source_name(self) -> str:
        return "greenhouse"

    def _random_delay(self) -> float:
        return random.uniform(GREENHOUSE_DELAY_MIN, GREENHOUSE_DELAY_MAX)

    async def _fetch_board_jobs(self, client: httpx.AsyncClient, board: str) -> List[Dict[str, Any]]:
        jobs = []
        page = 1

        while len(jobs) < GREENHOUSE_MAX_JOBS:
            url = f"{API_BASE}/{board}/jobs?per_page=100&page={page}"
            try:
                resp = await client.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT / 1000)
                if resp.status_code == 404:
                    logger.debug("Board '%s' not found, skipping", board)
                    break
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.warning("Failed to fetch board '%s' page %d: %s", board, page, e)
                break

            items = data.get("jobs", [])
            if not items:
                break

            for item in items:
                title = (item.get("title") or "").strip()
                if not title:
                    continue

                offices = item.get("offices", [])
                location = "; ".join(o.get("name", "") for o in offices if o.get("name"))
                company = item.get("company_name") or board.title()
                departments = item.get("departments", [])
                dept_names = [d.get("name", "") for d in departments if d.get("name")]

                remote = any(
                    "remote" in (o.get("name", "") or "").lower()
                    or "remote" in (o.get("location", "") or "").lower()
                    for o in offices
                ) or any("remote" in d.lower() for d in dept_names)

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "remote": remote,
                    "description": "",
                    "salary_min": None,
                    "salary_max": None,
                    "salary_text": "",
                    "detail_url": item.get("absolute_url", ""),
                    "posted_at": item.get("first_published") or item.get("updated_at"),
                    "id": item.get("id"),
                    "board": board,
                    "departments": dept_names,
                    "tags": dept_names,
                })

            meta = data.get("meta", {})
            total = meta.get("total", 0)
            if page * 100 >= total:
                break
            page += 1

            if len(jobs) >= GREENHOUSE_MAX_JOBS:
                jobs = jobs[:GREENHOUSE_MAX_JOBS]
                break

        logger.info("Board '%s': %d jobs", board, len(jobs))
        return jobs

    async def _enrich_job(self, client: httpx.AsyncClient, job: Dict[str, Any]) -> Dict[str, Any]:
        board = job.get("board", "")
        job_id = job.get("id")
        if not board or not job_id:
            return job

        url = f"{API_BASE}/{board}/jobs/{job_id}"
        try:
            resp = await client.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT / 1000)
            resp.raise_for_status()
            detail = resp.json()
        except Exception as e:
            logger.debug("Failed to fetch detail for job %s/%s: %s", board, job_id, e)
            return job

        content = detail.get("content", "")
        if content:
            job["description"] = clean_html(content) or ""

        office_names = [o.get("name", "") for o in detail.get("offices", []) if o.get("name")]
        if office_names:
            job["location"] = "; ".join(office_names)

        location_obj = detail.get("location", {})
        if isinstance(location_obj, dict):
            loc_name = location_obj.get("name", "")
            if loc_name and not job["location"]:
                job["location"] = loc_name

        for m in detail.get("metadata", []):
            val = str(m.get("value", "")).lower()
            name = str(m.get("name", "")).lower()
            if "remote" in val or "remote" in name:
                job["remote"] = True

        updated = detail.get("updated_at") or detail.get("first_published")
        if updated:
            job["posted_at"] = updated

        return job

    async def fetch_raw(self) -> List[Dict[str, Any]]:
        self._collected = []
        logger.info("Greenhouse scraping started (%d boards)", len(GREENHOUSE_BOARDS))

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT / 1000) as client:
            for board in GREENHOUSE_BOARDS:
                if len(self._collected) >= GREENHOUSE_MAX_JOBS:
                    break
                logger.info("Fetching board: %s", board)
                jobs = await self._fetch_board_jobs(client, board)
                self._collected.extend(jobs)
                await asyncio.sleep(self._random_delay())

        logger.info("Total raw jobs from listing: %d", len(self._collected))

        if not self._collected:
            return self._collected

        sem = asyncio.Semaphore(GREENHOUSE_CONCURRENCY)

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT / 1000) as client:
            async def enrich_one(job: Dict[str, Any]) -> Dict[str, Any]:
                async with sem:
                    result = await self._enrich_job(client, job)
                    await asyncio.sleep(self._random_delay() * 0.5)
                    return result

            tasks = [enrich_one(job) for job in self._collected]
            results = await asyncio.gather(*tasks)

        logger.info("Enriched %d jobs with details", len(results))
        self._collected = results
        return self._collected

    def _infer_seniority(self, title: str, description: str) -> Optional[str]:
        text = (title + " " + (description or "")).lower()
        if any(w in text for w in ["junior", "jr", "júnior", "entry", "entry-level", "trainee", "estágio", "estagiario", "estagiário", "graduate"]):
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

    def _extract_tags(self, title: str, description: str, existing: List[str]) -> List[str]:
        tags = list(existing) if existing else []
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
            if kw in corpus and kw not in tags:
                tags.append(kw)
        return tags

    def parse(self, raw: Dict[str, Any]) -> Optional[ScrapedJob]:
        try:
            title = raw.get("title", "").strip()
            if not title or len(title) < 3:
                return None

            description = raw.get("description") or ""
            tags = self._extract_tags(title, description, raw.get("tags", []) or [])

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
                location=raw.get("location", "").strip() or "Remote",
                remote=raw.get("remote", False),
                description=truncate(description),
                tags=tags,
                job_url=raw.get("detail_url", ""),
                salary_min=salary_min,
                salary_max=salary_max,
                currency="USD",
                source=self.source_name(),
                seniority=seniority,
                employment_type=emp_type,
                posted_at=parse_date(raw.get("posted_at")),
            )
        except Exception as e:
            logger.warning("Failed to parse Greenhouse entry: %s", e)
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
