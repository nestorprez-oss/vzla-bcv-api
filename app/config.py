import os
from dotenv import load_dotenv

load_dotenv()

BCV_URL: str = os.getenv("BCV_URL", "https://www.bcv.org.ve/")
CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "15"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
RATE_LIMIT: str = os.getenv("RATE_LIMIT", "10/minute")
SCRAPER_USER_AGENT: str = os.getenv(
    "SCRAPER_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
)
VALID_CURRENCIES: set[str] = {"USD", "EUR"}
SOURCE_NAME: str = "BCV Official Site"
