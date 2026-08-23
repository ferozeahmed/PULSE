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
        # This logger owns its own handler/formatter; without disabling
        # propagation, any consumer that also configures Python logging (or
        # even just calls log_step() once, since that lazily attaches this
        # handler to the shared "pulse_tf" parent logger) would see every
        # subsequent pulse-tf log line duplicated: once via this handler and
        # once via propagation up to the root logger's handler.
        logger.propagate = False
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
