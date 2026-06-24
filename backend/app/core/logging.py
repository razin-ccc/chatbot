import logging
from logging.config import dictConfig
from pathlib import Path
import sys

log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "default",
            "filename": "logs/fastapi.log",
            "mode": "a",
            "maxBytes": 100 * 1024 * 1024,
            "backupCount": 10,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "app": {"handlers": ["file"], "level": "DEBUG", "propagate": False},
    },
    "root": {"handlers": ["console"], "level": "DEBUG"},
}
Path("logs").mkdir(parents=True, exist_ok=True)
dictConfig(log_config)
logger = logging.getLogger("app")
