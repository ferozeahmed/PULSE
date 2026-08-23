from __future__ import annotations

import logging

DEFAULT_REDACTED_KEYS = {"authorization", "password", "token", "api_key", "secret"}


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def redact(
    data: dict[str, str], *, redacted_keys: set[str] = DEFAULT_REDACTED_KEYS
) -> dict[str, str]:
    return {
        key: ("***REDACTED***" if key.lower() in redacted_keys else value)
        for key, value in data.items()
    }


def log_step(message: str, *, logger_name: str = "pulse_tf") -> None:
    get_logger(logger_name).info(message)
