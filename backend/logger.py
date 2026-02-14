"""Custom logger setup for the backend."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from threading import Lock
from typing import Dict, Optional

from dotenv import find_dotenv, load_dotenv

LOG_ENV_VAR = "LOG_LOCATION"
DEFAULT_LOG_PATH = "./llogs/reel_quick.log"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
INTEGRATION_LOGGERS = (
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
    "arq",
    "arq.worker",
)

_loggers: Dict[str, logging.Logger] = {}
_handlers: Dict[str, logging.FileHandler] = {}
_lock = Lock()


def _resolve_path(log_path: Optional[str]) -> Path:
    load_dotenv(find_dotenv())
    resolved_path = log_path or os.getenv(LOG_ENV_VAR, DEFAULT_LOG_PATH)
    path = Path(resolved_path)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _ensure_handler(path: Path) -> logging.FileHandler:
    key = str(path)
    handler = _handlers.get(key)
    if handler is None:
        handler = logging.FileHandler(path)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        _handlers[key] = handler
    return handler


def _attach_handler(logger: logging.Logger, handler: logging.FileHandler) -> None:
    has_handler = any(
        isinstance(existing, logging.FileHandler)
        and getattr(existing, "baseFilename", None) == handler.baseFilename
        for existing in logger.handlers
    )
    if not has_handler:
        logger.addHandler(handler)


def _configure_integrations(handler: logging.FileHandler) -> None:
    for logger_name in INTEGRATION_LOGGERS:
        integration_logger = logging.getLogger(logger_name)
        integration_logger.setLevel(logging.INFO)
        _attach_handler(integration_logger, handler)


def get_logger(
    log_path: Optional[str] = None,
    name: str = "instagram_reel_creation",
) -> logging.Logger:
    """Return a logger configured with a file handler."""
    path = _resolve_path(log_path)
    cache_key = f"{name}:{path}"

    with _lock:
        if cache_key in _loggers:
            return _loggers[cache_key]

        handler = _ensure_handler(path)
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        _attach_handler(logger, handler)
        _configure_integrations(handler)

        _loggers[cache_key] = logger
        return logger
