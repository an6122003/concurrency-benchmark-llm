"""App logging: console + rotating file in the platform log dir."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .paths import log_dir

_configured = False


def get_logger(name: str = "hardware_ai_benchmark") -> logging.Logger:
    global _configured
    logger = logging.getLogger(name)
    if not _configured:
        logger.setLevel(logging.DEBUG)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        file_handler = RotatingFileHandler(
            log_dir() / "app.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        logger.addHandler(console)
        logger.addHandler(file_handler)
        _configured = True
    return logger
