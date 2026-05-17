import sys
import os

INTERP = os.path.join(os.path.dirname(__file__), "venv", "bin", "python")
if os.path.exists(INTERP) and sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.insert(0, os.path.dirname(__file__))

from a2wsgi import ASGIMiddleware
from app.main import app

application = ASGIMiddleware(app)
