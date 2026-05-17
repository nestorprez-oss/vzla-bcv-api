📘 Guía de Implementación - BCV Exchange Rate API
API oficial no oficial del Banco Central de Venezuela para obtener tasas de cambio (USD/EUR)
https://img.shields.io/badge/License-MIT-yellow.svg
https://img.shields.io/badge/python-3.12+-blue.svg
https://img.shields.io/badge/FastAPI-0.136-green.svg

📋 Tabla de Contenidos
Características

Requisitos Previos

Instalación Local

Estructura del Proyecto

Despliegue en VPS (Recomendado)

Despliegue en Hosting Compartido (cPanel)

¿Por qué passenger_wsgi.py en cPanel?

¿VPS vs Hosting Compartido?

Endpoints de la API

Variables de Entorno

Solución de Problemas

Licencia

✨ Características
✅ Tasas de cambio USD y EUR del BCV

✅ Actualización automática con caché de 5 minutos

✅ Rate limiting (10 peticiones/minuto)

✅ Documentación interactiva en /docs

✅ Respuesta en menos de 1 segundo (caché)

✅ Logging estructurado en JSON

📦 Requisitos Previos
Python 3.12 o superior

pip (gestor de paquetes)

Git (opcional)

🖥️ Instalación Local
bash
# Clonar el repositorio
git clone https://github.com/tuusuario/bcv-exchange-api.git
cd bcv-exchange-api

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Copiar variables de entorno
cp .env.example .env

# Ejecutar la API
uvicorn app.main:app --reload --port 8000
Probar localmente:

bash
curl http://localhost:8000/api/v1/rates/usd
📁 Estructura del Proyecto
text
bcv-exchange-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app + CORS + lifespan
│   ├── config.py        # Configuración desde .env
│   ├── models.py        # Schemas Pydantic
│   ├── scraper.py       # Web scraping del BCV
│   ├── cache.py         # Caché en memoria con TTL
│   └── routes.py        # Endpoints de la API
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── passenger_wsgi.py    # Bridge ASGI→WSGI para cPanel
└── README.md
🚀 Despliegue en VPS (Recomendado)
¿Por qué VPS?
Ventaja	Descripción
Control total	Puedes abrir cualquier puerto (8000, 80, 443)
Sin bloqueos	No hay restricciones de red o firewall como en hosting compartido
Docker listo	Puedes usar contenedores fácilmente
Escalable	Puedes aumentar recursos cuando necesites
Costo	Desde $5-6 USD/mes (DigitalOcean, Vultr, Hetzner)
Opción 1: Despliegue Manual (Ubuntu 22.04/24.04)
bash
# Conectarte al VPS
ssh usuario@tu-vps-ip

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python y herramientas
sudo apt install python3-pip python3-venv nginx -y

# Clonar el repositorio
git clone https://github.com/tuusuario/bcv-exchange-api.git
cd bcv-exchange-api

# Crear entorno virtual e instalar dependencias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copiar .env
cp .env.example .env
nano .env  # Ajusta variables si es necesario

# Probar la API
uvicorn app.main:app --host 0.0.0.0 --port 8000
Crear servicio systemd (para que corra siempre):

bash
sudo nano /etc/systemd/system/bcv-api.service
ini
[Unit]
Description=BCV Exchange Rate API
After=network.target

[Service]
User=tu_usuario
WorkingDirectory=/home/tu_usuario/bcv-exchange-api
Environment="PATH=/home/tu_usuario/bcv-exchange-api/venv/bin"
ExecStart=/home/tu_usuario/bcv-exchange-api/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
bash
sudo systemctl daemon-reload
sudo systemctl enable bcv-api
sudo systemctl start bcv-api
sudo systemctl status bcv-api
Configurar Nginx como proxy inverso (opcional, para quitar el puerto 8000):

bash
sudo nano /etc/nginx/sites-available/bcv-api
nginx
server {
    listen 80;
    server_name api.tudominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
bash
sudo ln -s /etc/nginx/sites-available/bcv-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
Opción 2: Despliegue con Docker (Más fácil)
bash
# Instalar Docker
curl -fsSL https://get.docker.com | sudo bash
sudo usermod -aG docker $USER
# Cerrar sesión y volver a entrar

# Construir y ejecutar
cd bcv-exchange-api
docker-compose up -d
La API estará disponible en: http://tu-vps-ip:8000

🖥️ Despliegue en Hosting Compartido (cPanel)
⚠️ Limitaciones del Hosting Compartido
Limitación	Impacto
Puertos bloqueados	No puedes acceder desde internet directamente
Sin mod_proxy	No puedes redirigir tráfico a Uvicorn
Passenger no soporta ASGI	Problemas con FastAPI
Por qué usamos passenger_wsgi.py
El problema: cPanel usa Phusion Passenger para ejecutar aplicaciones Python, pero Passenger está diseñado para WSGI (Flask, Django), no para ASGI (FastAPI).

La solución: passenger_wsgi.py actúa como un puente (bridge) que convierte ASGI a WSGI usando la librería a2wsgi.

python
# passenger_wsgi.py
from a2wsgi import ASGIMiddleware
from app.main import app

# Passenger espera una variable llamada 'application'
application = ASGIMiddleware(app)
Sin este bridge, Passenger no puede ejecutar FastAPI.

Paso a paso en cPanel
Subir archivos a /home/usuario/bcv.vzla.studio/

En cPanel:

Entrar a "Setup Python App"

Crear nueva aplicación:

Python version: 3.12

Application root: bcv.vzla.studio

Application URL: bcv.vzla.studio

Application startup file: passenger_wsgi.py

Application Entry point: application

Instalar dependencias (en el virtualenv de cPanel):

bash
/home/usuario/virtualenv/bcv.vzla.studio/3.12/bin/pip install -r requirements.txt
Configurar variables de entorno en cPanel (o subir .env)

Reiniciar la aplicación

⚠️ Nota sobre Hosting Compartido
La API solo será accesible localmente (127.0.0.1:8000) porque los puertos están bloqueados. Para consumirla desde internet, necesitas:

Opción A: Usar un túnel (ngrok, Serveo, Cloudflare Tunnel)

Opción B: Consumirla desde otra app en el mismo servidor usando http://127.0.0.1:8000/api/v1/rates/usd

Recomendación: Si necesitas acceso público, usa un VPS.

🆚 VPS vs Hosting Compartido
Característica	VPS ($5-6/mes)	Hosting Compartido ($3-5/mes)
Puerto 8000 accesible	✅ Sí	❌ No (bloqueado)
FastAPI (ASGI)	✅ Soporte nativo	⚠️ Necesita bridge (inestable)
mod_proxy	✅ Disponible	❌ Normalmente deshabilitado
Control total	✅ Root access	❌ Limitado
Docker	✅ Sí	❌ No
Escalabilidad	✅ Alta	❌ Baja
Túneles (ngrok)	✅ No necesarios	⚠️ Necesarios para acceso externo
Configuración	Media	Baja (guiada)
Recomendación
Para producción: VPS (DigitalOcean, Vultr, Hetzner) desde $5/mes

Para pruebas locales o apps internas: Hosting compartido (solo si la app que consume la API está en el mismo servidor)

🌐 Endpoints de la API
Método	Endpoint	Descripción
GET	/	Información del servicio
GET	/health	Health check
GET	/api/v1/rates/usd	Tasa de cambio USD
GET	/api/v1/rates/eur	Tasa de cambio EUR
GET	/api/v1/rates	Todas las tasas
GET	/docs	Documentación Swagger UI
GET	/redoc	Documentación ReDoc
Ejemplo de respuesta
json
{
  "currency": "USD",
  "rate": 517.9619,
  "source": "BCV Official Site",
  "last_updated": "2026-05-17T18:57:46.672263+00:00",
  "cache_age_seconds": 0
}
🔧 Variables de Entorno (.env)
env
BCV_URL=https://www.bcv.org.ve/
CACHE_TTL_SECONDS=300
REQUEST_TIMEOUT=15
LOG_LEVEL=INFO
RATE_LIMIT=10/minute
SCRAPER_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
Variable	Descripción	Default
BCV_URL	URL del sitio del BCV	https://www.bcv.org.ve/
CACHE_TTL_SECONDS	Tiempo de vida de la caché (segundos)	300
REQUEST_TIMEOUT	Timeout para scraping (segundos)	15
LOG_LEVEL	Nivel de logging (DEBUG, INFO, WARNING, ERROR)	INFO
RATE_LIMIT	Límite de peticiones	10/minute
SCRAPER_USER_AGENT	User-Agent para el scraper	Mozilla/5.0 ...
🐛 Solución de Problemas
Error: ModuleNotFoundError: No module named 'slowapi'
bash
pip install slowapi
Error: SSL certificate verify failed
python
# En scraper.py, añadir verify=False
resp = _SESSION.get(url, timeout=timeout, verify=False)
Error: Passenger no encuentra la aplicación
Verificar que passenger_wsgi.py está en la raíz

Verificar Entry Point = application

Verificar que a2wsgi está instalado

El puerto 8000 no es accesible desde internet
En VPS: Abrir puerto en el firewall

En hosting compartido: Usar túnel (ngrok) o consumir desde localhost

📄 Licencia
MIT License - Libre para usar, modificar y distribuir.

🙏 Créditos
Banco Central de Venezuela - Fuente de los datos

FastAPI - Framework web

BeautifulSoup4 - Web scraping

a2wsgi - Bridge ASGI→WSGI

📞 Soporte
Abre un issue en GitHub

Revisa la documentación en /docs
