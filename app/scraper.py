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


def _extract_rate(html: str, currency: str) -> float:
    soup = BeautifulSoup(html, "html.parser")
    currency = currency.upper()

    elements = soup.select(".strong-tb")
    if not elements:
        raise ValueError("No se encontraron elementos .strong-tb en el HTML del BCV")

    idx = _CURRENCY_INDEX.get(currency)
    if idx is None:
        raise ValueError(f"Moneda '{currency}' no encontrada en el indice del BCV")

    if idx >= len(elements):
        raise ValueError(
            f"Indice {idx} fuera de rango para {currency} (solo {len(elements)} elementos)"
        )

    raw_value = elements[idx].text.strip().replace(",", ".")
    value = float(raw_value)
    if not 0.1 < value < 10000:
        raise ValueError(f"Valor {value} fuera de rango esperado para {currency}")
    return value


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
