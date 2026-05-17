from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ScrapedJob:
    title: str
    company: str
    location: str
    remote: bool
    description: str
    tags: List[str]
    job_url: str
    salary_min: float | None
    salary_max: float | None
    currency: str
    source: str
    seniority: str | None
    employment_type: str | None
    posted_at: str | None


class BaseScraper(ABC):
    @abstractmethod
    async def fetch_raw(self) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    def parse(self, raw: Dict[str, Any]) -> ScrapedJob | None:
        ...

    @abstractmethod
    def source_name(self) -> str:
        ...
