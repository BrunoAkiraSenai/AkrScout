import asyncio
import random
import re
from typing import Any, Dict, List, Optional

import httpx

from config.settings import (
    REQUEST_TIMEOUT,
    WWR_CATEGORIES,
    WWR_DELAY_MAX,
    WWR_DELAY_MIN,
    WWR_MAX_JOBS,
)
from parsers.skill_extractor import SkillExtractor
from services.supabase import DatabaseService
from utils.logger import setup_logger
from utils.normalizer import clean_html, parse_date, parse_salary, truncate

from .base import BaseScraper, ScrapedJob

logger = setup_logger("weworkremotely")

RSS_BASE = "https://weworkremotely.com/categories"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


class WeWorkRemotelyScraper(BaseScraper):
    def __init__(self, db: DatabaseService):
        self._db = db
        self._skill_extractor = SkillExtractor()
        self._collected: List[Dict[str, Any]] = []

    def source_name(self) -> str:
        return "weworkremotely"

    def _random_delay(self) -> float:
        return random.uniform(WWR_DELAY_MIN, WWR_DELAY_MAX)

    async def fetch_raw(self) -> List[Dict[str, Any]]:
        self._collected = []
        logger.info("WeWorkRemotely scraping started (%d categories)", len(WWR_CATEGORIES))

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT / 1000) as client:
            for category in WWR_CATEGORIES:
                if len(self._collected) >= WWR_MAX_JOBS:
                    break

                url = f"{RSS_BASE}/{category}.rss"
                logger.info("Fetching category: %s", category)

                try:
                    resp = await client.get(url, headers=HEADERS, follow_redirects=True)
                    if resp.status_code != 200:
                        logger.warning("RSS '%s' returned %d", category, resp.status_code)
                        continue
                except Exception as e:
                    logger.warning("Failed to fetch RSS '%s': %s", category, e)
                    continue

                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "xml")
                items = soup.find_all("item")

                for item in items:
                    if len(self._collected) >= WWR_MAX_JOBS:
                        break

                    title_raw = item.find("title")
                    if not title_raw:
                        continue
                    title_raw = title_raw.text.strip()

                    company, title = self._split_company_title(title_raw)
                    if not title or len(title) < 3:
                        continue

                    link = item.find("link")
                    job_url = link.text.strip() if link else ""

                    desc_raw = item.find("description")
                    description = clean_html(desc_raw.text) if desc_raw else ""

                    pub_date = item.find("pubDate")
                    posted_at = pub_date.text.strip() if pub_date else None

                    salary_min, salary_max = None, None
                    salary_text = ""
                    if description:
                        salary_match = re.search(
                            r'\$[\d,]+(?:[\s-]+\$?[\d,]+)?(?:\s*(?:USD|k|K))?',
                            description,
                        )
                        if salary_match:
                            salary_text = salary_match.group()
                            salary_min, salary_max = parse_salary(salary_text)

                    remote = True

                    self._collected.append({
                        "title": title,
                        "company": company,
                        "location": "Remote",
                        "remote": remote,
                        "description": description,
                        "salary_min": salary_min,
                        "salary_max": salary_max,
                        "salary_text": salary_text,
                        "detail_url": job_url,
                        "posted_at": posted_at,
                        "tags": [],
                    })

                logger.info("Category '%s': %d jobs", category, len(items))
                await asyncio.sleep(self._random_delay())

        logger.info("WeWorkRemotely collected %d raw entries", len(self._collected))
        return self._collected

    def _split_company_title(self, raw: str) -> tuple:
        idx = raw.find(": ")
        if idx > 0:
            return raw[:idx].strip(), raw[idx + 2:].strip()
        return "Unknown", raw.strip()

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
            if kw in corpus and kw not in tags:
                tags.append(kw)
        return tags

    def parse(self, raw: Dict[str, Any]) -> Optional[ScrapedJob]:
        try:
            title = raw.get("title", "").strip()
            if not title or len(title) < 3:
                return None

            description = raw.get("description") or ""
            tags = self._extract_tags(title, description)

            salary_min = raw.get("salary_min")
            salary_max = raw.get("salary_max")

            seniority = self._infer_seniority(title, description)
            emp_type = self._infer_employment_type(title, description)

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
            logger.warning("Failed to parse WeWorkRemotely entry: %s", e)
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
