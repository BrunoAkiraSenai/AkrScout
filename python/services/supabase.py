import hashlib
import re
from typing import List, Optional

from supabase import Client, create_client

from config.settings import SUPABASE_SERVICE_KEY, SUPABASE_URL
from parsers.skill_extractor import SkillExtractor
from utils.logger import setup_logger

logger = setup_logger("db")


class DatabaseService:
    def __init__(self):
        self._client: Client = create_client(
            SUPABASE_URL, SUPABASE_SERVICE_KEY
        )
        self._skill_cache: dict[str, str] = {}

    def _log_err(self, msg: str, exc: Optional[Exception] = None) -> None:
        logger.error(msg)
        if exc:
            logger.debug(exc, exc_info=True)

    # ── Companies ──────────────────────────────────────────────────────

    def get_or_create_company(self, name: str) -> Optional[str]:
        name = name.strip()
        if not name:
            return None

        try:
            result = (
                self._client.table("companies")
                .select("id")
                .ilike("name", name)
                .limit(1)
                .execute()
            )
            if result.data:
                return result.data[0]["id"]

            resp = (
                self._client.table("companies")
                .insert({"name": name})
                .execute()
            )
            return resp.data[0]["id"]
        except Exception as e:
            self._log_err(f"Failed to get/create company '{name}'", e)
            return None

    # ── Skills ─────────────────────────────────────────────────────────

    def load_skills(self) -> dict[str, str]:
        try:
            result = (
                self._client.table("skills")
                .select("slug, id")
                .execute()
            )
            self._skill_cache = {
                self._normalize_slug(row["slug"]): row["id"]
                for row in result.data
            }
            logger.info("Loaded %d skills from database", len(self._skill_cache))
            return self._skill_cache
        except Exception as e:
            self._log_err("Failed to load skills from database", e)
            return {}

    def _normalize_slug(self, slug: str) -> str:
        slug = slug.lower().strip()
        slug = slug.replace(".", "-").replace("#", "sharp").replace("/", "-")
        slug = slug.replace(" ", "-").replace("_", "-")
        slug = re.sub(r"-+", "-", slug).strip("-")
        return slug

    def get_or_create_skill(self, slug: str) -> Optional[str]:
        slug = self._normalize_slug(slug)
        if slug in self._skill_cache:
            return self._skill_cache[slug]

        try:
            display_name = slug.replace("-", " ").title()
            resp = (
                self._client.table("skills")
                .insert({"name": display_name, "slug": slug})
                .execute()
            )
            skill_id = resp.data[0]["id"]
            self._skill_cache[slug] = skill_id
            logger.info("Created new skill: %s (%s)", slug, skill_id)
            return skill_id
        except Exception as e:
            self._log_err(f"Failed to create skill '{slug}'", e)
            return None

    def ensure_skills(self, slugs: List[str]) -> List[str]:
        ids: List[str] = []
        for slug in slugs:
            sid = self.get_or_create_skill(slug)
            if sid:
                ids.append(sid)
        return ids

    # ── Jobs ────────────────────────────────────────────────────────────

    def upsert_job(self, job: dict) -> Optional[str]:
        try:
            row = {k.removeprefix('p_'): v for k, v in job.items()}
            row['content_hash'] = hashlib.md5(
                f"{row.get('title', '').lower().strip()}"
                f"::{row.get('company_id', '')}"
                f"::{row.get('location', '')}".encode()
            ).hexdigest()

            existing = (
                self._client.table("jobs")
                .select("id")
                .eq("content_hash", row["content_hash"])
                .limit(1)
                .execute()
            )

            if existing.data:
                job_id = existing.data[0]["id"]
                self._client.table("jobs").update(row).eq("id", job_id).execute()
            else:
                result = self._client.table("jobs").insert(row).execute()
                job_id = result.data[0]["id"] if result.data else None

            if job_id:
                logger.debug("Upserted job: %s → %s", job.get("title", "?"), job_id)
            return job_id
        except Exception as e:
            self._log_err(f"Failed to upsert job '{job.get('p_title', '?')}'", e)
            return None

    def attach_skills(self, job_id: str, skill_slugs: List[str]) -> None:
        if not skill_slugs:
            return
        skill_ids = self.ensure_skills(skill_slugs)
        if not skill_ids:
            return
        try:
            self._client.rpc("fn_set_job_skills", {
                "p_job_id": job_id,
                "p_skill_ids": skill_ids,
            }).execute()
            logger.debug("Attached %d skills to job %s", len(skill_ids), job_id)
        except Exception as e:
            self._log_err(f"Failed to attach skills to job {job_id}", e)

    # ── Analytics snapshot ─────────────────────────────────────────────

    def generate_snapshot(self) -> None:
        try:
            top_skills = (
                self._client.from_("vw_top_skills")
                .select("name, demand_count")
                .limit(10)
                .execute()
            )
            top_companies = (
                self._client.from_("vw_top_companies")
                .select("name, job_count")
                .limit(10)
                .execute()
            )
            remote = (
                self._client.from_("vw_remote_stats")
                .select("remote_percentage")
                .execute()
            )

            self._client.table("analytics_snapshots").insert({
                "top_skills": top_skills.data,
                "top_companies": top_companies.data,
                "remote_percentage": remote.data[0]["remote_percentage"] if remote.data else 0,
            }).execute()
            logger.info("Analytics snapshot generated")
        except Exception as e:
            self._log_err("Failed to generate analytics snapshot", e)

    # ── Health ─────────────────────────────────────────────────────────

    def health(self) -> bool:
        try:
            self._client.table("skills").select("id").limit(1).execute()
            return True
        except Exception:
            return False
