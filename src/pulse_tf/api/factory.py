from __future__ import annotations

import pytest

from pulse_tf.api.base_client import BaseAPIClient
from pulse_tf.config.settings import PulseSettings
from pulse_tf.exceptions import PulseConfigError


class APIClientFactory:
    def __init__(self, settings: PulseSettings) -> None:
        self._settings = settings
        self._registry: dict[str, type[BaseAPIClient]] = {}
        self._instances: dict[str, BaseAPIClient] = {}

    def register(self, name: str, client_cls: type[BaseAPIClient]) -> None:
        self._registry[name] = client_cls

    def create(self, name: str) -> BaseAPIClient:
        if name in self._instances:
            return self._instances[name]
        if name not in self._registry:
            raise PulseConfigError(f"No API client registered for '{name}'")
        base_url = self._settings.api_base_urls.get(name)
        if base_url is None:
            raise PulseConfigError(
                f"No base_url configured for '{name}' in pulse_settings.api_base_urls"
            )
        instance = self._registry[name](base_url)
        self._instances[name] = instance
        return instance


@pytest.fixture(scope="session")
def api_factory(pulse_settings: PulseSettings) -> APIClientFactory:
    return APIClientFactory(pulse_settings)
