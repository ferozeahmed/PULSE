from __future__ import annotations

from typing import Literal

import pytest
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from pulse_tf.exceptions import PulseConfigError


class PulseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PULSE_", env_file=".env", extra="ignore")

    environment: Literal["dev", "staging", "prod"] = "dev"
    base_url: str = "http://localhost"
    api_base_urls: dict[str, str] = {}
    browser: Literal["chromium", "firefox", "webkit"] = "chromium"
    headless: bool = True
    default_timeout: int = 30000
    allure_results_dir: str = "allure-results"
    log_level: str = "INFO"


def load_settings(settings_cls: type[PulseSettings] = PulseSettings) -> PulseSettings:
    try:
        return settings_cls()
    except ValidationError as exc:
        raise PulseConfigError(str(exc)) from exc


@pytest.fixture(scope="session")
def pulse_settings() -> PulseSettings:
    return load_settings()
