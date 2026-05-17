from pydantic import BaseModel


class RateResponse(BaseModel):
    currency: str
    rate: float
    source: str
    last_updated: str
    cache_age_seconds: int


class RatesResponse(BaseModel):
    rates: dict[str, RateResponse]
    source: str
    cache_age_seconds: int
