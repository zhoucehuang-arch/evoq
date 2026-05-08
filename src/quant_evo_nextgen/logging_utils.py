from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        event_payload = getattr(record, "event_payload", None)
        if isinstance(event_payload, dict):
            payload.update(event_payload)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: int | None = None) -> None:
    log_format = os.getenv("QE_LOG_FORMAT", "json").strip().lower()
    level_name = os.getenv("QE_LOG_LEVEL", "INFO").strip().upper()
    effective_level = level if level is not None else getattr(logging, level_name, logging.INFO)
    handler = logging.StreamHandler()
    if log_format == "text":
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    else:
        handler.setFormatter(JsonLogFormatter())

    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
    else:
        root.handlers = [handler]
    root.setLevel(effective_level)


def log_event(logger: logging.Logger, event_type: str, **fields: Any) -> None:
    payload = {"event_type": event_type, **fields}
    logger.info(event_type, extra={"event_payload": payload})
