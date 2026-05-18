import asyncio
import time
import sys

from analytics.tracker import PipelineTracker
from scrapers.programathor import ProgramathorScraper
from scrapers.greenhouse import GreenhouseScraper
from scrapers.remotive import RemotiveScraper
from services.supabase import DatabaseService
from utils.logger import setup_logger

logger = setup_logger()

SCRAPERS = [
    ProgramathorScraper,
    GreenhouseScraper,
    RemotiveScraper,
]


async def run_scraper(db, scraper_cls, tracker) -> int:
    scraper = scraper_cls(db)
    logger.info("Scraping source: %s", scraper.source_name())
    start = time.monotonic()

    try:
        inserted = await scraper.run()
        elapsed = time.monotonic() - start
        logger.info(
            "Inserted %d jobs from %s (%.2fs)",
            inserted,
            scraper.source_name(),
            elapsed,
        )
        return inserted
    except Exception as e:
        logger.error(
            "Scraping failed for %s: %s", scraper.source_name(), e, exc_info=True
        )
        return 0


async def run_pipeline() -> None:
    tracker = PipelineTracker()
    tracker.start()

    logger.info("=" * 56)
    logger.info("  AKR Scout — Job Ingestion Pipeline")
    logger.info("=" * 56)

    db = DatabaseService()
    if not db.health():
        logger.error("Supabase connection failed. Check SUPABASE_URL and SUPABASE_SERVICE_KEY.")
        sys.exit(1)
    logger.info("Supabase connection OK")

    db.load_skills()

    total_inserted = 0
    for scraper_cls in SCRAPERS:
        inserted = await run_scraper(db, scraper_cls, tracker)
        total_inserted += inserted

    try:
        db.generate_snapshot()
    except Exception as e:
        logger.warning("Analytics snapshot failed: %s", e)

    result = tracker.stop()

    logger.info("-" * 56)
    logger.info("  Pipeline Summary")
    logger.info("  Sources:   %d", len(SCRAPERS))
    logger.info("  Inserted:  %d", total_inserted)
    logger.info("  Duration:  %.2fs", result.elapsed)
    logger.info("=" * 56)


def main() -> None:
    asyncio.run(run_pipeline())


if __name__ == "__main__":
    main()
