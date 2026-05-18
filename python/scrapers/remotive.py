import asyncio
import random
from typing import Any, Dict, List, Optional

import httpx

from config.settings import (
    REMOTIVE_API_URL,
    REMOTIVE_CATEGORIES,
    REMOTIVE_DELAY_MAX,
    REMOTIVE_DELAY_MIN,
    REMOTIVE_MAX_JOBS,
    REQUEST_TIMEOUT,
)
from parsers.skill_extractor import SkillExtractor
from services.supabase import DatabaseService
from utils.logger import setup_logger
from utils.normalizer import clean_html, parse_date, parse_salary, truncate

from .base import BaseScraper, ScrapedJob

logger = setup_logger("remotive")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


class RemotiveScraper(BaseScraper):
    def __init__(self, db: DatabaseService):
        self._db = db
        self._skill_extractor = SkillExtractor()
        self._collected: List[Dict[str, Any]] = []

    def source_name(self) -> str:
        return "remotive"

    def _random_delay(self) -> float:
        return random.uniform(REMOTIVE_DELAY_MIN, REMOTIVE_DELAY_MAX)

    async def fetch_raw(self) -> List[Dict[str, Any]]:
        self._collected = []
        logger.info("Remotive scraping started (%d categories)", len(REMOTIVE_CATEGORIES))

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT / 1000) as client:
            for category in REMOTIVE_CATEGORIES:
                if len(self._collected) >= REMOTIVE_MAX_JOBS:
                    break

                url = f"{REMOTIVE_API_URL}?limit=100&category={category}"
                logger.info("Fetching category: %s", category)

                try:
                    resp = await client.get(url, headers=HEADERS)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    logger.warning("Failed to fetch category '%s': %s", category, e)
                    continue

                jobs = data.get("jobs", [])
                logger.info("Category '%s': %d jobs", category, len(jobs))

                for j in jobs:
                    if len(self._collected) >= REMOTIVE_MAX_JOBS:
                        break

                    title = (j.get("title") or "").strip()
                    if not title or len(title) < 3:
                        continue

                    location = (j.get("candidate_required_location") or "").strip()
                    loc_lower = location.lower()
                    brazil_ok = any(k in loc_lower for k in [
                        "worldwide", "anywhere", "global", "remote",
                        "americas", "latin america", "latam", "south america",
                        "brazil", "brasil",
                    ])
                    if not brazil_ok:
                        continue

                    remote = True

                    company = (j.get("company_name") or "").strip()
                    if not company:
                        company = "Unknown"

                    salary_text = (j.get("salary") or "").strip()
                    salary_min, salary_max = None, None
                    if salary_text:
                        salary_min, salary_max = parse_salary(salary_text)

                    description = clean_html(j.get("description") or "") or ""

                    tags = j.get("tags") or []

                    self._collected.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "remote": remote,
                        "description": description,
                        "salary_min": salary_min,
                        "salary_max": salary_max,
                        "salary_text": salary_text,
                        "detail_url": j.get("url", ""),
                        "posted_at": j.get("publication_date"),
                        "tags": tags,
                        "job_type": j.get("job_type"),
                    })

                await asyncio.sleep(self._random_delay())

        logger.info("Remotive collected %d raw entries", len(self._collected))
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

    def _infer_employment_type(self, raw_type: Optional[str], title: str, description: str) -> Optional[str]:
        text = (title + " " + (description or "")).lower()
        if raw_type:
            t = raw_type.lower()
            if "full" in t or "permanent" in t:
                return "full_time"
            if "part" in t:
                return "part_time"
            if "contract" in t:
                return "contract"
            if "intern" in t:
                return "internship"
        if any(w in text for w in ["part time", "part-time", "meio periodo", "meio período"]):
            return "part_time"
        if any(w in text for w in ["contract", "freelance", "freela", "pj", "temporary", "temp", "autônomo", "autonomo"]):
            return "contract"
        if any(w in text for w in ["intern", "internship", "estágio", "estagiario", "estagiário", "trainee"]):
            return "internship"
        return "full_time"

    def _extract_tags(self, title: str, description: str, existing: List[str]) -> List[str]:
        seen = set(existing) if existing else set()
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
            if kw in corpus and kw not in seen:
                seen.add(kw)
        return list(seen)

    def parse(self, raw: Dict[str, Any]) -> Optional[ScrapedJob]:
        try:
            title = raw.get("title", "").strip()
            if not title or len(title) < 3:
                return None

            description = raw.get("description") or ""
            tags = self._extract_tags(title, description, raw.get("tags", []) or [])

            salary_min = raw.get("salary_min")
            salary_max = raw.get("salary_max")

            emp_type = self._infer_employment_type(raw.get("job_type"), title, description)
            seniority = self._infer_seniority(title, description)

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
                currency="USD",
                source=self.source_name(),
                seniority=seniority,
                employment_type=emp_type,
                posted_at=parse_date(raw.get("posted_at")),
            )
        except Exception as e:
            logger.warning("Failed to parse Remotive entry: %s", e)
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
