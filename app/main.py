import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app import config
from app.logging_config import setup_logging
from app.rate_limit import limiter
from app.routes import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging(config.LOG_LEVEL)
    logger.info(
        "Server starting: BCV_URL=%s CACHE_TTL=%ds TIMEOUT=%ds RATE_LIMIT=%s CURRENCIES=%s",
        config.BCV_URL,
        config.CACHE_TTL_SECONDS,
        config.REQUEST_TIMEOUT,
        config.RATE_LIMIT,
        sorted(config.VALID_CURRENCIES),
    )
    yield
    logger.info("Server shutting down")


app = FastAPI(
    title="VZLA BCV API",
    description="API para consultar tasas de cambio oficiales publicadas por el Banco Central de Venezuela (BCV) mediante web scraping con caché en memoria.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "VZLA BCV API",
        "version": "1.0.0",
        "description": "Tasas de cambio oficiales del BCV",
        "endpoints": {
            "usd": "/api/v1/rates/usd",
            "eur": "/api/v1/rates/eur",
            "all": "/api/v1/rates",
        },
        "supported_currencies": sorted(config.VALID_CURRENCIES),
        "cache_ttl_seconds": config.CACHE_TTL_SECONDS,
        "rate_limit": config.RATE_LIMIT,
        "docs": "/docs",
    }
