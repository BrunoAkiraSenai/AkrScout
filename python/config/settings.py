import os

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

REMOTEOK_API_URL = "https://remoteok.com/api"
REMOTEOK_PAGE_URL = "https://remoteok.com"

PROGRAMATHOR_LISTING_URL = "https://programathor.com.br/jobs"
PROGRAMATHOR_BASE_URL = "https://programathor.com.br"
PROGRAMATHOR_MAX_PAGES = 3
PROGRAMATHOR_CONCURRENCY = 5

REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"
REMOTIVE_CATEGORIES = ["software-dev", "devops", "data", "artificial-intelligence"]
REMOTIVE_MAX_JOBS = 50
REMOTIVE_DELAY_MIN = 0.5
REMOTIVE_DELAY_MAX = 1.5

GREENHOUSE_BOARDS = [
    "vercel", "stripe", "airbnb", "datadog",
    "discord", "notion", "linear",
]
GREENHOUSE_MAX_JOBS = 50
GREENHOUSE_CONCURRENCY = 5
GREENHOUSE_DELAY_MIN = 0.5
GREENHOUSE_DELAY_MAX = 1.5

REQUEST_TIMEOUT = 30000
MAX_RETRIES = 3
BROWSER_HEADLESS = True
