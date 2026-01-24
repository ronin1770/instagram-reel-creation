"""Custom logger setup for the backend."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import find_dotenv, load_dotenv

LOG_ENV_VAR = "LOG_LOCATION"
DEFAULT_LOG_PATH = "./log/backend.log"

_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """Return a singleton logger configured with a file handler."""
    global _logger
    if _logger is not None:
        return _logger

    load_dotenv(find_dotenv())
    log_path = os.getenv(LOG_ENV_VAR, DEFAULT_LOG_PATH)
    path = Path(log_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("instagram_reel_creation")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler(path)
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    _logger = logger
    return logger
