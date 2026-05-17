# VZLA BCV API

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://docker.com)

API REST no oficial para consultar las **tasas de cambio oficiales** (USD/EUR) publicadas por el **Banco Central de Venezuela (BCV)**.

> ⚠️ **Nota:** El BCV no ofrece una API oficial. Esta implementación utiliza web scraping con estrategias de fallback para ser resistente a cambios en la estructura HTML del sitio.

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Inicio Rápido](#-inicio-rápido)
- [Endpoints de la API](#-endpoints-de-la-api)
- [Variables de Entorno](#-variables-de-entorno)
- [Despliegue en VPS](#-despliegue-en-vps-recomendado)
- [Despliegue en cPanel](#-despliegue-en-cpanel-hosting-compartido)
- [¿Por qué `passenger_wsgi.py`?](#-por-qué-passenger_wsgipy)
- [Solución de Problemas](#-solución-de-problemas)
- [Licencia](#-licencia)

---

## ✨ Características

| Característica | Descripción |
|----------------|-------------|
| 💰 **Tasas USD/EUR** | Obtén las tasas oficiales del BCV en tiempo real |
| ⚡ **Caché inteligente** | TTL configurable (default: 5 min) para no sobrecargar el BCV |
| 🚦 **Rate limiting** | Límite configurable (default: 10 req/min) por IP |
| 📚 **Documentación automática** | Swagger UI en `/docs` y ReDoc en `/redoc` |
| 🔒 **Logging estructurado** | Formato JSON para fácil integración con herramientas de monitoreo |
| 🐳 **Docker listo** | `Dockerfile` + `docker-compose.yml` para producción |
| 🔧 **Bridge ASGI→WSGI** | `passenger_wsgi.py` para compatibilidad con cPanel |
| 🛡️ **Web scraping directo** | Extracción vía `.strong-tb` del DOM real del BCV, probado en producción |

---

## 📁 Estructura del Proyecto

```
vzla-bcv-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + lifespan
│   ├── config.py            # Configuración desde variables de entorno
│   ├── models.py            # Schemas Pydantic (RateResponse, RatesResponse)
│   ├── scraper.py           # Web scraping del BCV via .strong-tb
│   ├── cache.py             # Caché en memoria con TTL y stale data
│   ├── routes.py            # Handlers de los endpoints
│   ├── rate_limit.py        # Rate limiting por IP
│   └── logging_config.py    # Logging estructurado en JSON
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── passenger_wsgi.py        # Bridge ASGI→WSGI para cPanel
└── README.md
```

---

## 🚀 Inicio Rápido

### Opción 1: Docker (Recomendado para producción)

```bash
git clone https://github.com/nestorprez-oss/vzla-bcv-api.git
cd vzla-bcv-api
cp .env.example .env
docker compose up -d
```

### Opción 2: Local (Desarrollo)

```bash
git clone https://github.com/nestorprez-oss/vzla-bcv-api.git
cd vzla-bcv-api
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Probar la API

```bash
curl http://localhost:8000/api/v1/rates/usd
```

---

## 🌐 Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Metadatos de la API |
| `GET` | `/api/v1/rates/usd` | Tasa de cambio USD |
| `GET` | `/api/v1/rates/eur` | Tasa de cambio EUR |
| `GET` | `/api/v1/rates` | Todas las tasas |
| `GET` | `/docs` | Swagger UI (interactivo) |
| `GET` | `/redoc` | Documentación ReDoc |

### Respuesta ejemplo (`/api/v1/rates/usd`)

```json
{
  "currency": "USD",
  "rate": 517.9619,
  "source": "BCV Official Site",
  "last_updated": "2026-05-17T18:57:46.672263+00:00",
  "cache_age_seconds": 0
}
```

### Respuesta ejemplo (`/api/v1/rates`)

```json
{
  "rates": {
    "USD": {
      "currency": "USD",
      "rate": 517.9619,
      "source": "BCV Official Site",
      "last_updated": "2026-05-17T18:57:46.672263+00:00",
      "cache_age_seconds": 0
    },
    "EUR": {
      "currency": "EUR",
      "rate": 602.18768455,
      "source": "BCV Official Site",
      "last_updated": "2026-05-17T18:57:46.672263+00:00",
      "cache_age_seconds": 0
    }
  },
  "source": "BCV Official Site",
  "cache_age_seconds": 0
}
```

---

## 🔧 Variables de Entorno (`.env`)

```env
BCV_URL=https://www.bcv.org.ve/
CACHE_TTL_SECONDS=300
REQUEST_TIMEOUT=15
LOG_LEVEL=INFO
RATE_LIMIT=10/minute
```

| Variable | Default | Descripción |
|----------|---------|-------------|
| `BCV_URL` | `https://www.bcv.org.ve/` | URL del sitio del BCV |
| `CACHE_TTL_SECONDS` | `300` | Tiempo de vida de la caché (segundos) |
| `REQUEST_TIMEOUT` | `15` | Timeout para el scraping (segundos) |
| `LOG_LEVEL` | `INFO` | Nivel de logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `RATE_LIMIT` | `10/minute` | Límite de peticiones por IP |

---

## 🖥️ Despliegue en VPS (Recomendado)

### ¿Por qué VPS?

| Ventaja | Descripción |
|---------|-------------|
| Puertos abiertos | Puedes acceder a tu API desde internet sin túneles |
| Control total | Root access para instalar lo que necesites |
| Docker listo | Puedes usar contenedores sin restricciones |
| Costo | Desde $5-6 USD/mes (DigitalOcean, Vultr, Hetzner) |

### Paso a paso (Ubuntu 22.04/24.04)

```bash
# Conectarse al VPS
ssh usuario@tu-vps-ip

# Actualizar e instalar dependencias
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx docker.io docker-compose

# Clonar y ejecutar con Docker
git clone https://github.com/nestorprez-oss/vzla-bcv-api.git
cd vzla-bcv-api
cp .env.example .env
docker compose up -d
```

La API estará disponible en: `http://tu-vps-ip:8000`

### Opción: Sin Docker (servicio systemd)

```bash
# Crear servicio systemd
sudo nano /etc/systemd/system/bcv-api.service
```

```ini
[Unit]
Description=BCV Exchange Rate API
After=network.target

[Service]
User=tu_usuario
WorkingDirectory=/home/tu_usuario/vzla-bcv-api
Environment="PATH=/home/tu_usuario/vzla-bcv-api/venv/bin"
ExecStart=/home/tu_usuario/vzla-bcv-api/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable bcv-api
sudo systemctl start bcv-api
```

---

## 🖥️ Despliegue en cPanel (Hosting Compartido)

### ⚠️ Limitaciones del Hosting Compartido

| Limitación | Impacto |
|------------|---------|
| Puertos bloqueados | La API solo es accesible desde `127.0.0.1` (local) |
| Sin `mod_proxy` | No se puede redirigir tráfico público |
| Passenger no soporta ASGI | Necesitas el bridge `passenger_wsgi.py` |

### 🔧 ¿Por qué `passenger_wsgi.py`?

cPanel usa **Phusion Passenger** que solo entiende aplicaciones WSGI (Flask, Django). FastAPI es **ASGI**. `passenger_wsgi.py` es un puente (bridge) que convierte ASGI → WSGI usando `a2wsgi`.

```python
# passenger_wsgi.py
from a2wsgi import ASGIMiddleware
from app.main import app

# Passenger espera una variable llamada 'application'
application = ASGIMiddleware(app)
```

### 📝 Configuración paso a paso

1. Sube los archivos a `/home/usuario/bcv.vzla.studio/`

2. En **cPanel**:
   - Ve a **"Setup Python App"**
   - Crea una nueva aplicación con:
     - **Python version:** 3.12
     - **Application root:** `bcv.vzla.studio`
     - **Application URL:** `bcv.vzla.studio`
     - **Application startup file:** `passenger_wsgi.py`
     - **Application Entry point:** `application`

3. Instala dependencias:

```bash
/home/usuario/virtualenv/bcv.vzla.studio/3.12/bin/pip install -r requirements.txt
```

4. Configura variables de entorno en cPanel o sube `.env`

5. Reinicia la aplicación

### 🚨 Nota sobre accesibilidad

En hosting compartido, la API solo es accesible localmente (`http://127.0.0.1:8000`). Si otra aplicación en el mismo servidor necesita consumirla, funciona perfectamente. Para acceso público, usa un túnel (`ngrok`, `Serveo`) o migra a un VPS.

---

## 🆚 VPS vs Hosting Compartido

| Característica | VPS ($5-6/mes) | Hosting Compartido ($3-5/mes) |
|----------------|-----------------|-------------------------------|
| Puerto 8000 accesible desde internet | ✅ Sí | ❌ No (bloqueado) |
| FastAPI (ASGI) nativo | ✅ Soporte total | ⚠️ Necesita bridge (`passenger_wsgi.py`) |
| Docker | ✅ Sí | ❌ No |
| Control total | ✅ Root access | ❌ Limitado |
| `mod_proxy` disponible | ✅ Sí | ❌ Generalmente no |
| Recomendado para | Producción | Apps internas en el mismo servidor |

**Recomendación:** Si necesitas acceso público, usa un **VPS**. Si la API es solo para otras apps en el mismo servidor, hosting compartido es suficiente.

---

## 🐛 Solución de Problemas

### Error: `ModuleNotFoundError: No module named 'slowapi'`

```bash
pip install slowapi
```

### Error: SSL certificate verify failed

El servidor no verifica el certificado SSL del BCV. Se soluciona agregando `verify=False` en `scraper.py`:

```python
resp = _SESSION.get(url, timeout=timeout, verify=False)
```

### Error: Passenger no encuentra la aplicación (cPanel)

- Verifica que `passenger_wsgi.py` está en la raíz del proyecto
- Verifica que el Entry Point es `application`
- Verifica que `a2wsgi` está instalado: `pip install a2wsgi`

### Error: El puerto 8000 no es accesible

- **En VPS:** Abre el puerto en el firewall: `sudo ufw allow 8000`
- **En hosting compartido:** No es posible. Usa un túnel (`ngrok`) o consume desde `localhost`.

---

## 📄 Licencia

MIT © 2026 Nestor Perez https://vzla.studio

---

## 🙏 Créditos

- [Banco Central de Venezuela](https://www.bcv.org.ve/) - Fuente de los datos
- [FastAPI](https://fastapi.tiangolo.com) - Framework web
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) - Web scraping
- [a2wsgi](https://github.com/abersheeran/a2wsgi) - Bridge ASGI→WSGI

---

## 📞 Soporte

- Abre un [issue](https://github.com/nestorprez-oss/vzla-bcv-api/issues) en GitHub
- Revisa la documentación interactiva en `/docs`