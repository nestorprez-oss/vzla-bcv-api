# VZLA BCV API

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)

API REST para consultar las tasas de cambio oficiales publicadas por el Banco Central de Venezuela (BCV).

## Características

- **Web scraping** de la página oficial del BCV con `beautifulsoup4`
- **Caché en memoria** con TTL configurable (default: 5 minutos)
- **Rate limiting** por IP (default: 10 requests/minuto)
- **Logging estructurado en JSON** con niveles DEBUG/INFO/WARNING/ERROR
- **Docker** listo para producción con `Dockerfile` + `docker-compose.yml`
- **Compatibilidad con Phusion Passenger** (`passenger_wsgi.py`)

## Stack

| Componente | Tecnología |
|------------|------------|
| Framework | FastAPI |
| Server | Uvicorn |
| Scraping | Requests + BeautifulSoup4 |
| Rate Limiting | SlowAPI |
| Container | Docker + Compose |

## Inicio rápido

### Con Docker (recomendado)

```bash
git clone https://github.com/nestorprez-oss/vzla-bcv-api.git
cd vzla-bcv-api
docker compose up -d
```

### Sin Docker

```bash
git clone https://github.com/nestorprez-oss/vzla-bcv-api.git
cd vzla-bcv-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/` | Metadatos de la API |
| `GET` | `/api/v1/rates/usd` | Tasa USD |
| `GET` | `/api/v1/rates/eur` | Tasa EUR |
| `GET` | `/api/v1/rates` | Todas las tasas |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/redoc` | ReDoc |

## Respuesta

### `GET /api/v1/rates/usd`

```json
{
  "currency": "USD",
  "rate": 517.9619,
  "source": "BCV Official Site",
  "last_updated": "2026-05-17T15:36:01Z",
  "cache_age_seconds": 0
}
```

### `GET /api/v1/rates`

```json
{
  "rates": {
    "USD": {
      "currency": "USD",
      "rate": 517.9619,
      "source": "BCV Official Site",
      "last_updated": "2026-05-17T15:36:01Z",
      "cache_age_seconds": 0
    },
    "EUR": {
      "currency": "EUR",
      "rate": 602.1876,
      "source": "BCV Official Site",
      "last_updated": "2026-05-17T15:36:01Z",
      "cache_age_seconds": 0
    }
  },
  "source": "BCV Official Site",
  "cache_age_seconds": 0
}
```

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `BCV_URL` | `https://www.bcv.org.ve/` | URL del BCV a scrapear |
| `CACHE_TTL_SECONDS` | `300` | Tiempo de vida de la caché (segundos) |
| `REQUEST_TIMEOUT` | `15` | Timeout del request al BCV (segundos) |
| `LOG_LEVEL` | `INFO` | Nivel de logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `RATE_LIMIT` | `10/minute` | Límite de requests por IP |

Copiá `.env.example` a `.env` y ajustá los valores según necesites.

## Despliegue

### Docker Compose

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CACHE_TTL_SECONDS=600
      - RATE_LIMIT=20/minute
    restart: unless-stopped
```

### Phusion Passenger

El archivo `passenger_wsgi.py` expone la app FastAPI como WSGI mediante `a2wsgi`. Passenger lo detecta automáticamente por la variable `application`.

## Licencia

MIT © 2026 [Nestor Perez](https://vzla.studio)
