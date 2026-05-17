import asyncio
import time
import sys

from analytics.tracker import PipelineTracker
from scrapers.remoteok import RemoteOKScraper
from services.supabase import DatabaseService
from utils.logger import setup_logger

logger = setup_logger()


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

    scraper = RemoteOKScraper(db)
    logger.info("Scraping source: %s", scraper.source_name())

    try:
        inserted = await scraper.run()
        logger.info("Inserted %d jobs from %s", inserted, scraper.source_name())
    except Exception as e:
        logger.error("Scraping failed: %s", e, exc_info=True)
        sys.exit(1)

    try:
        db.generate_snapshot()
    except Exception as e:
        logger.warning("Analytics snapshot failed: %s", e)

    result = tracker.stop()

    logger.info("-" * 56)
    logger.info("  Pipeline Summary")
    logger.info("  Found:     %d", result.total_found)
    logger.info("  Inserted:  %d", result.inserted)
    logger.info("  Skipped:   %d", result.skipped)
    logger.info("  Errors:    %d", result.errors)
    logger.info("  Duration:  %.2fs", result.elapsed)
    logger.info("=" * 56)


def main() -> None:
    asyncio.run(run_pipeline())


if __name__ == "__main__":
    main()
