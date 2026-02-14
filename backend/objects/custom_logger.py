import logging

from backend.logger import get_logger as get_backend_logger


def get_logger(name: str = "instagram_post_creator") -> logging.Logger:
    """Return a backend logger configured to write to the shared log file."""
    logger = get_backend_logger(name=name)
    logger.setLevel(logging.INFO)
    return logger
