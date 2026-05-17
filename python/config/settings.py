import os

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

REMOTEOK_API_URL = "https://remoteok.com/api"
REMOTEOK_PAGE_URL = "https://remoteok.com"

REQUEST_TIMEOUT = 30000
MAX_RETRIES = 3
BROWSER_HEADLESS = True
