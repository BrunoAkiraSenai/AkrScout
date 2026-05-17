"""
Temporary script to populate database with real jobs.
Uses direct HTTP request instead of Playwright (which needs system deps).
"""
import urllib.request
import json
import sys
sys.path.insert(0, '.')

from utils.logger import setup_logger
from services.supabase import DatabaseService
from parsers.skill_extractor import SkillExtractor
from utils.normalizer import parse_salary, parse_date, clean_html, truncate

logger = setup_logger()

def fetch_api():
    req = urllib.request.Request(
        'https://remoteok.com/api',
        headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
    )
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read())
    if isinstance(data, list) and len(data) > 1 and 'slug' not in data[0]:
        data = data[1:]
    return data

def infer_seniority(title, description):
    text = (title + ' ' + (description or '')).lower()
    if any(w in text for w in ['junior', 'jr', 'entry', 'trainee', 'graduate']):
        return 'junior'
    if any(w in text for w in ['senior', 'sr', 'staff', 'principal', 'lead']):
        return 'senior'
    if any(w in text for w in ['mid', 'intermediate', 'mid-level']):
        return 'mid'
    return None

def infer_employment_type(title, description):
    text = (title + ' ' + (description or '')).lower()
    if any(w in text for w in ['part time', 'part-time']):
        return 'part_time'
    if any(w in text for w in ['contract', 'freelance', 'temporary']):
        return 'contract'
    if any(w in text for w in ['intern', 'internship']):
        return 'internship'
    return 'full_time'

def main():
    logger.info('=' * 56)
    logger.info('  AKR Scout — Seed Populate')
    logger.info('=' * 56)

    db = DatabaseService()
    if not db.health():
        logger.error('Supabase connection failed')
        sys.exit(1)
    logger.info('Supabase connection OK')

    db.load_skills()
    extractor = SkillExtractor()

    raw = fetch_api()
    logger.info('Fetched %d jobs from API', len(raw))

    inserted = 0
    for i, entry in enumerate(raw):
        try:
            title = entry.get('position', '').strip()
            if not title:
                continue

            company = entry.get('company', '').strip() or 'Unknown'
            company_id = db.get_or_create_company(company)
            if not company_id:
                continue

            description = clean_html(entry.get('description', '')) or ''
            tags = entry.get('tags', []) or []
            salary_min, salary_max = parse_salary(entry.get('salary'))

            slug = entry.get('slug', '')
            job_url = entry.get('url') or f'https://remoteok.com/remote-jobs/{slug}' if slug else ''

            posted = parse_date(entry.get('date'))

            job_data = {
                'p_company_id': company_id,
                'p_title': title,
                'p_description': truncate(description),
                'p_location': entry.get('location', '').strip() or 'Remote',
                'p_remote': True,
                'p_seniority': infer_seniority(title, description),
                'p_employment_type': infer_employment_type(title, description),
                'p_salary_min': salary_min,
                'p_salary_max': salary_max,
                'p_currency': 'USD',
                'p_job_url': job_url,
                'p_source': 'remoteok',
                'p_posted_at': posted,
            }

            job_id = db.upsert_job(job_data)
            if job_id:
                slugs = extractor.extract(tags, description or '')
                db.attach_skills(job_id, slugs)
                inserted += 1
                logger.info('[%d/%d] + %s @ %s', i + 1, len(raw), title, company)
        except Exception as e:
            logger.warning('Failed entry %d: %s', i, e)

    try:
        db.generate_snapshot()
    except Exception as e:
        logger.warning('Snapshot failed: %s', e)

    logger.info('-' * 56)
    logger.info('  Inserted: %d jobs', inserted)
    logger.info('=' * 56)

if __name__ == '__main__':
    main()
