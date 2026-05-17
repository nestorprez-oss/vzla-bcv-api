import time
import logging
from threading import Lock
from typing import Optional, Tuple, Any
from app import config

logger = logging.getLogger(__name__)


class Cache:
    def __init__(self, ttl: int | None = None):
        self._ttl = ttl if ttl is not None else config.CACHE_TTL_SECONDS
        self._data: dict[str, dict[str, Any]] = {}
        self._timestamps: dict[str, float] = {}
        self._lock = Lock()
        logger.debug("Cache initialized TTL=%ds", self._ttl)

    def get(self, key: str) -> Tuple[Optional[dict], int, bool]:
        with self._lock:
            if key not in self._data:
                logger.debug("Cache MISS key=%s", key)
                return None, 0, False
            age = time.time() - self._timestamps[key]
            fresh = age < self._ttl
            if fresh:
                logger.debug("Cache HIT key=%s age=%ds", key, int(age))
            else:
                logger.debug("Cache STALE key=%s age=%ds", key, int(age))
            return self._data[key], int(age), fresh

    def set(self, key: str, value: dict) -> None:
        with self._lock:
            self._data[key] = value
            self._timestamps[key] = time.time()
            logger.debug("Cache SET key=%s", key)

    def all_fresh(self, keys: list[str]) -> bool:
        with self._lock:
            now = time.time()
            stale = []
            missing = []
            for key in keys:
                if key not in self._timestamps:
                    missing.append(key)
                elif now - self._timestamps[key] >= self._ttl:
                    stale.append(f"{key}(age={int(now - self._timestamps[key])}s)")
            if missing or stale:
                logger.debug(
                    "Cache not fresh missing=%s stale=%s",
                    missing or [],
                    stale or [],
                )
                return False
            logger.debug("All cache fresh keys=%s", keys)
            return True

    def get_all(self, keys: list[str]) -> dict[str, Tuple[Optional[dict], int, bool]]:
        result = {}
        for key in keys:
            result[key] = self.get(key)
        return result


cache = Cache()
