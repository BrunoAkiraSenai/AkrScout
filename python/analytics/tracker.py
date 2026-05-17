import time
from dataclasses import dataclass, field
from typing import List


@dataclass
class PipelineResult:
    total_found: int = 0
    inserted: int = 0
    skipped: int = 0
    errors: int = 0
    elapsed: float = 0.0
    details: List[str] = field(default_factory=list)


class PipelineTracker:
    def __init__(self):
        self._start: float = 0.0
        self._result = PipelineResult()

    def start(self) -> None:
        self._start = time.monotonic()

    def stop(self) -> PipelineResult:
        self._result.elapsed = time.monotonic() - self._start
        return self._result

    def found(self, n: int = 1) -> None:
        self._result.total_found += n

    def inserted(self, title: str) -> None:
        self._result.inserted += 1
        self._result.details.append(f"+ {title}")

    def skipped(self, title: str, reason: str = "duplicate") -> None:
        self._result.skipped += 1
        self._result.details.append(f"~ {title} ({reason})")

    def error(self, title: str, exc: str) -> None:
        self._result.errors += 1
        self._result.details.append(f"! {title} → {exc}")
