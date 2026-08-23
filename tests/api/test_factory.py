import pytest

from pulse_tf.api.base_client import BaseAPIClient
from pulse_tf.api.factory import APIClientFactory
from pulse_tf.config.settings import PulseSettings
from pulse_tf.exceptions import PulseConfigError


class FakeClient(BaseAPIClient):
    pass


@pytest.fixture
def settings():
    return PulseSettings(api_base_urls={"users": "https://users.test"})


def test_create_returns_registered_client(settings):
    factory = APIClientFactory(settings)
    factory.register("users", FakeClient)
    client = factory.create("users")
    assert isinstance(client, FakeClient)
    assert client.base_url == "https://users.test"


def test_create_caches_instance(settings):
    factory = APIClientFactory(settings)
    factory.register("users", FakeClient)
    assert factory.create("users") is factory.create("users")


def test_create_unregistered_service_raises(settings):
    factory = APIClientFactory(settings)
    with pytest.raises(PulseConfigError):
        factory.create("unknown")


def test_create_without_base_url_raises(settings):
    factory = APIClientFactory(settings)
    factory.register("orders", FakeClient)
    with pytest.raises(PulseConfigError):
        factory.create("orders")


def test_api_factory_fixture_is_available(api_factory):
    assert isinstance(api_factory, APIClientFactory)
