import atexit
import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from pathlib import Path
from queue import Queue
from typing import Any

from core.config import getSettings


REQUEST_ID_CTX: ContextVar[str] = ContextVar("request_id", default="-")
USER_ID_CTX: ContextVar[str] = ContextVar("user_id", default="-")

_RESERVED_RECORD_FIELDS = set(logging.makeLogRecord({}).__dict__.keys())
_RESERVED_RECORD_FIELDS.update({"message", "asctime"})


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = REQUEST_ID_CTX.get("-")
        record.user_id = USER_ID_CTX.get("-")
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "request_id": getattr(record, "request_id", "-"),
            "user_id": getattr(record, "user_id", "-"),
        }

        if hasattr(record, "event"):
            payload["event"] = record.event
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _RESERVED_RECORD_FIELDS
            and key
            not in {
                "request_id",
                "user_id",
                "event",
                "exc_text",
                "stack_info",
            }
        }
        if extra_fields:
            payload["extra"] = extra_fields
        return json.dumps(payload, ensure_ascii=False)


def set_request_context(request_id: str, user_id: str | None = None) -> None:
    REQUEST_ID_CTX.set(request_id or "-")
    USER_ID_CTX.set(user_id or "-")


def clear_request_context() -> None:
    REQUEST_ID_CTX.set("-")
    USER_ID_CTX.set("-")


def get_request_id() -> str:
    return REQUEST_ID_CTX.get("-")


def log_event(
    event: str, message: str, level: int = logging.INFO, **fields: Any
) -> None:
    logger.log(level, message, extra={"event": event, **fields})


def stop_logging_listener() -> None:
    global _QUEUE_LISTENER
    if _QUEUE_LISTENER is not None:
        _QUEUE_LISTENER.stop()
        _QUEUE_LISTENER = None


try:
    settings = getSettings()
    environment = settings.ENVIRONMENT
    log_queue_size = settings.LOG_QUEUE_SIZE
except Exception:
    # Keep logging resilient in early bootstrapping contexts.
    environment = "local"
    log_queue_size = 10000

log_level = "DEBUG" if environment == "local" else "INFO"
_QUEUE_LISTENER: QueueListener | None = None


def _configure_logging() -> logging.Logger:
    global _QUEUE_LISTENER

    Path("logs").mkdir(parents=True, exist_ok=True)

    request_context_filter = RequestContextFilter()
    json_formatter = JsonFormatter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(json_formatter)

    file_handler = RotatingFileHandler(
        filename="logs/fastapi.log",
        mode="a",
        maxBytes=100 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.setLevel("INFO")
    file_handler.setFormatter(json_formatter)

    log_queue: Queue[logging.LogRecord] = Queue(maxsize=log_queue_size)
    queue_handler = QueueHandler(log_queue)
    queue_handler.setLevel(log_level)
    # Inject request/user context before enqueue so listener thread preserves it.
    queue_handler.addFilter(request_context_filter)

    app_logger = logging.getLogger("app")
    app_logger.handlers = [queue_handler]
    app_logger.setLevel(log_level)
    app_logger.propagate = False

    root_logger = logging.getLogger()
    root_logger.handlers = [queue_handler]
    root_logger.setLevel(log_level)

    if _QUEUE_LISTENER is not None:
        _QUEUE_LISTENER.stop()
    _QUEUE_LISTENER = QueueListener(
        log_queue,
        console_handler,
        file_handler,
        respect_handler_level=True,
    )
    _QUEUE_LISTENER.start()
    return app_logger


logger = _configure_logging()
atexit.register(stop_logging_listener)
