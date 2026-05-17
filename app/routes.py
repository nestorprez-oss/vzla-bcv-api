import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from app import config
from app.cache import cache
from app.models import RateResponse, RatesResponse
from app.rate_limit import limiter
from app.scraper import scrape

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")


def _refresh_all_cached() -> dict[str, float] | None:
    logger.info("Cache refresh triggered")
    try:
        data = scrape()
    except RuntimeError as e:
        logger.error("Cache refresh failed: %s", e)
        return None
    now = datetime.now(timezone.utc).isoformat()
    for cur, rate in data.items():
        cache.set(cur, {"rate": rate, "source": config.SOURCE_NAME, "last_updated": now})
    logger.info("Cache refreshed rates=%s", {cur: data[cur] for cur in data})
    return data


def _stale_response(currency: str, entry: dict, age: int) -> RateResponse:
    return RateResponse(
        currency=currency,
        rate=entry["rate"],
        source=entry["source"],
        last_updated=entry["last_updated"],
        cache_age_seconds=age,
    )


def _fresh_response(currency: str, rate: float, now: str) -> RateResponse:
    return RateResponse(
        currency=currency,
        rate=rate,
        source=config.SOURCE_NAME,
        last_updated=now,
        cache_age_seconds=0,
    )


def _get_or_refresh(currency: str) -> RateResponse:
    currency = currency.upper()
    if currency not in config.VALID_CURRENCIES:
        logger.warning("Rejected unsupported currency: %s", currency)
        raise HTTPException(
            status_code=404,
            detail=f"Moneda '{currency}' no soportada. Usar: {', '.join(sorted(config.VALID_CURRENCIES))}",
        )

    cached_entry, age, fresh = cache.get(currency)

    if fresh:
        logger.debug("Serving cached %s age=%ds", currency, age)
        return _stale_response(currency, cached_entry, age)

    logger.info("Cache stale for %s, refreshing all", currency)
    data = _refresh_all_cached()

    if data is not None and currency in data:
        now = datetime.now(timezone.utc).isoformat()
        logger.info("Fresh %s=%s", currency, data[currency])
        return _fresh_response(currency, data[currency], now)

    if cached_entry is not None:
        logger.warning("Serving stale %s (scrape failed) age=%ds", currency, age)
        return _stale_response(currency, cached_entry, age)

    logger.error("No data for %s: cache empty and scrape failed", currency)
    raise HTTPException(
        status_code=502,
        detail="No se pudo obtener la tasa del BCV y no hay datos en caché",
    )


@router.get("/rates/{currency}", response_model=RateResponse)
@limiter.limit(config.RATE_LIMIT)
def get_rate(request: Request, currency: str):
    logger.info("GET /rates/%s", currency)
    return _get_or_refresh(currency)


@router.get("/rates", response_model=RatesResponse)
@limiter.limit(config.RATE_LIMIT)
def get_all_rates(request: Request):
    if not cache.all_fresh(list(config.VALID_CURRENCIES)):
        logger.info("GET /rates - cache not fresh, triggering refresh")
        _refresh_all_cached()
    else:
        logger.debug("GET /rates - all cache fresh")

    rates = {}
    max_age = 0

    for key in config.VALID_CURRENCIES:
        entry, age, fresh = cache.get(key)
        if entry is not None:
            rates[key] = RateResponse(
                currency=key,
                rate=entry["rate"],
                source=entry["source"],
                last_updated=entry["last_updated"],
                cache_age_seconds=age,
            )
            if age > max_age:
                max_age = age

    if not rates:
        logger.error("GET /rates - no data in cache")
        raise HTTPException(
            status_code=502,
            detail="No hay datos disponibles en caché",
        )

    logger.debug("Returning %d rates max_age=%ds", len(rates), max_age)
    return RatesResponse(
        rates=rates,
        source=config.SOURCE_NAME,
        cache_age_seconds=max_age,
    )
