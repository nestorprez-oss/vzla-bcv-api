import re
import logging
import requests
import urllib3
from bs4 import BeautifulSoup
from app import config

logger = logging.getLogger(__name__)

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
})

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_CURRENCY_INDEX = {
    "EUR": 0,
    "CNY": 1,
    "TRY": 2,
    "RUB": 3,
    "USD": 4,
}

_LABELS = {
    "USD": ["USD", "DOLAR", "DÓLAR"],
    "EUR": ["EUR", "EURO"],
    "CNY": ["CNY", "YUAN"],
    "TRY": ["TRY", "LIRA"],
    "RUB": ["RUB", "RUBLO"],
}

_NUMBER_RE = re.compile(r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+))")


def _parse_decimal(raw: str) -> float:
    raw = raw.strip()
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        raw = raw.replace(",", ".")
    return float(raw)


def _extract_number(text: str) -> float | None:
    match = _NUMBER_RE.search(text)
    if match:
        val = _parse_decimal(match.group(1))
        if 0.1 < val < 10000:
            return val
    return None


def _matches_label(text: str, currency: str) -> bool:
    return any(label in text.upper() for label in _LABELS.get(currency, [currency]))


# ── Strategy 1: .strong-tb por indice fijo (primaria) ────────────────────────

def _try_strong_tb_index(soup: BeautifulSoup, currency: str) -> float | None:
    elements = soup.select(".strong-tb")
    if not elements:
        return None

    idx = _CURRENCY_INDEX.get(currency)
    if idx is None:
        return None

    if idx >= len(elements):
        logger.debug(
            ".strong-tb index %d out of range for %s (%d elements)",
            idx,
            currency,
            len(elements),
        )
        return None

    return _extract_number(elements[idx].text)


# ── Strategy 2: .strong-tb por label en el DOM (fallback si cambia el orden) ─

def _try_strong_tb_label(soup: BeautifulSoup, currency: str) -> float | None:
    elements = soup.select(".strong-tb")
    if not elements:
        return None

    for el in elements:
        wrapper = el.parent
        if wrapper:
            wrapper_text = wrapper.get_text(" ", strip=True)
            if _matches_label(wrapper_text, currency):
                return _extract_number(el.text)

        for ancestor in el.parents:
            if ancestor.name in ("html", "body", "main", "article", "section"):
                break
            ancestor_text = ancestor.get_text(" ", strip=True)
            num = _extract_number(el.text)
            if num is None:
                continue
            for label in _LABELS.get(currency, [currency]):
                pattern = re.compile(
                    rf"{re.escape(label)}\s*{re.escape(str(num).replace('.', ','))}",
                    re.IGNORECASE,
                )
                if pattern.search(ancestor_text):
                    return num
                pattern_dot = re.compile(
                    rf"{re.escape(label)}\s*{re.escape(str(num))}",
                    re.IGNORECASE,
                )
                if pattern_dot.search(ancestor_text):
                    return num

    logger.debug(".strong-tb found but no label match for %s", currency)
    return None


# ── Strategy 3: regex currency + numero sobre texto completo ─────────────────

def _try_regex_scan(soup: BeautifulSoup, currency: str) -> float | None:
    text = soup.get_text(" ", strip=True)

    patterns = {
        "USD": [
            rf"USD\s*(\d{{1,3}}(?:[.,]\d{{3}})*(?:[.,]\d+))",
            rf"D[OÓ]LAR\s*(\d{{1,3}}(?:[.,]\d{{3}})*(?:[.,]\d+))",
        ],
        "EUR": [
            rf"EUR\s*(\d{{1,3}}(?:[.,]\d{{3}})*(?:[.,]\d+))",
            rf"EURO\s*(\d{{1,3}}(?:[.,]\d{{3}})*(?:[.,]\d+))",
        ],
        "CNY": [
            rf"CNY\s*(\d{{1,3}}(?:[.,]\d{{3}})*(?:[.,]\d+))",
            rf"YUAN\s*(\d{{1,3}}(?:[.,]\d{{3}})*(?:[.,]\d+))",
        ],
        "TRY": [
            rf"TRY\s*(\d{{1,3}}(?:[.,]\d{{3}})*(?:[.,]\d+))",
            rf"LIRA\s*(\d{{1,3}}(?:[.,]\d{{3}})*(?:[.,]\d+))",
        ],
        "RUB": [
            rf"RUB\s*(\d{{1,3}}(?:[.,]\d{{3}})*(?:[.,]\d+))",
            rf"RUBLO\s*(\d{{1,3}}(?:[.,]\d{{3}})*(?:[.,]\d+))",
        ],
    }

    for pattern in patterns.get(currency, []):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return _parse_decimal(match.group(1))

    return None


# ── Strategy 4: elemento con label + numero en sibling o padre ───────────────

def _try_label_proximity(soup: BeautifulSoup, currency: str) -> float | None:
    candidates = soup.find_all(
        lambda tag: tag.name in ("td", "th", "div", "span", "strong", "p", "li", "label")
        and _matches_label(tag.get_text(), currency)
    )

    for el in candidates:
        for target in [
            el.find_next_sibling(),
            el.find_previous_sibling(),
        ]:
            if target and hasattr(target, "get_text"):
                num = _extract_number(target.get_text(strip=True))
                if num is not None:
                    return num

        parent = el.parent
        if parent and hasattr(parent, "get_text"):
            parent_text = parent.get_text(" ", strip=True)
            for label in _LABELS.get(currency, [currency]):
                idx = parent_text.upper().find(label)
                if idx >= 0:
                    tail = parent_text[idx + len(label):]
                    num = _extract_number(tail)
                    if num is not None:
                        return num

    return None


# ── Extraction orchestration ──────────────────────────────────────────────────

_STRATEGIES = [
    ("strong_tb_index", _try_strong_tb_index),
    ("strong_tb_label", _try_strong_tb_label),
    ("regex_scan", _try_regex_scan),
    ("label_proximity", _try_label_proximity),
]


def _extract_rate(html: str, currency: str) -> float:
    soup = BeautifulSoup(html, "html.parser")
    currency = currency.upper()

    logger.debug("Extracting %s with %d strategies", currency, len(_STRATEGIES))

    for name, strategy in _STRATEGIES:
        try:
            result = strategy(soup, currency)
            if result is not None:
                logger.debug("Strategy %s found %s=%s", name, currency, result)
                return result
            logger.debug("Strategy %s returned None for %s", name, currency)
        except Exception:
            logger.warning(
                "Strategy %s failed for %s", name, currency, exc_info=True
            )

    logger.error("All strategies failed for %s", currency)
    raise ValueError(f"No se pudo encontrar la tasa para {currency} en el HTML del BCV")


# ── Public API ────────────────────────────────────────────────────────────────

def scrape() -> dict[str, float]:
    logger.info("Fetching BCV rates from %s timeout=%ds", config.BCV_URL, config.REQUEST_TIMEOUT)

    try:
        resp = _SESSION.get(config.BCV_URL, timeout=config.REQUEST_TIMEOUT, verify=False)
        resp.raise_for_status()
    except requests.Timeout:
        logger.error("BCV request timed out after %ds", config.REQUEST_TIMEOUT)
        raise RuntimeError("El sitio del BCV no respondio a tiempo (timeout)")
    except requests.ConnectionError as e:
        logger.error("BCV connection failed: %s", e)
        raise RuntimeError("No se pudo conectar al sitio del BCV")
    except requests.HTTPError as e:
        logger.error("BCV returned HTTP %s", e.response.status_code)
        raise RuntimeError(f"El sitio del BCV retorno HTTP {e.response.status_code}")

    logger.info(
        "BCV responded HTTP %s %d bytes %.2fs",
        resp.status_code,
        len(resp.text),
        resp.elapsed.total_seconds(),
    )

    html = resp.text
    if not html or len(html) < 500:
        logger.warning("BCV returned insufficient content (%d bytes)", len(html) if html else 0)
        raise RuntimeError("El sitio del BCV retorno contenido vacio o insuficiente")

    rates = {}
    errors = []
    for currency in config.VALID_CURRENCIES:
        try:
            rates[currency] = _extract_rate(html, currency)
            logger.info("Extracted %s=%s", currency, rates[currency])
        except ValueError as e:
            logger.warning("Failed to extract %s: %s", currency, e)
            errors.append(str(e))

    if not rates:
        logger.error("All currencies failed errors=%s", errors)
        raise RuntimeError(
            "No se pudo extraer ninguna tasa: " + "; ".join(errors)
        )
    return rates
