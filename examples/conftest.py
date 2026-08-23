import pytest

from examples.api.clients.user_client import UserServiceClient
from pulse_tf.api.factory import APIClientFactory
from pulse_tf.config.settings import PulseSettings


@pytest.fixture(scope="session")
def pulse_settings() -> PulseSettings:
    return PulseSettings(api_base_urls={"users": "https://users.example"})


@pytest.fixture(autouse=True, scope="session")
def _register_clients(api_factory: APIClientFactory) -> None:
    api_factory.register("users", UserServiceClient)
