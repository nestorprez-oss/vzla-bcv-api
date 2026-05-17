import logging
import json
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "function": record.funcName,
        }
        if record.exc_info and record.exc_info[1]:
            payload["exception"] = str(record.exc_info[1])
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)

    logging.getLogger("uvicorn.error").handlers.clear()
    logging.getLogger("uvicorn.error").addHandler(handler)
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").addHandler(handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("bs4").setLevel(logging.WARNING)
