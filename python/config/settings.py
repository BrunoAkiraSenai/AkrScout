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

INDEED_SEARCH_URL = "https://br.indeed.com/jobs"
INDEED_SEARCH_QUERIES = ["desenvolvedor", "tecnologia", "engenheiro de software", "analista de sistemas"]
INDEED_MAX_PAGES = 2
INDEED_MAX_JOBS = 50
INDEED_DELAY_MIN = 3
INDEED_DELAY_MAX = 7
INDEED_PAGE_DELAY_MIN = 5
INDEED_PAGE_DELAY_MAX = 10

REQUEST_TIMEOUT = 30000
MAX_RETRIES = 3
BROWSER_HEADLESS = True
