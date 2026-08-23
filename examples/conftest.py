import http.server
import threading
from pathlib import Path

import pytest

from examples.api.clients.user_client import UserServiceClient
from pulse_tf.api.factory import APIClientFactory
from pulse_tf.config.settings import PulseSettings

# examples/web's static test pages live under examples/web/fixtures/; the
# server that serves them is started here (rather than in
# examples/web/conftest.py) so that the single pulse_settings fixture below
# can carry both base_url (for web) and api_base_urls (for api) at once. See
# the "Running differently-configured suites: separate invocations" section
# of README.md for why there must be exactly one pulse_settings fixture
# across all of examples/.
FIXTURES_DIR = Path(__file__).parent / "web" / "fixtures"


@pytest.fixture(scope="session")
def _static_server():
    def handler(*args, **kwargs):
        return http.server.SimpleHTTPRequestHandler(*args, directory=str(FIXTURES_DIR), **kwargs)

    server = http.server.ThreadingHTTPServer(("localhost", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()


@pytest.fixture(scope="session")
def pulse_settings(_static_server) -> PulseSettings:
    host, port = _static_server.server_address
    return PulseSettings(
        base_url=f"http://{host}:{port}",
        api_base_urls={"users": "https://users.example"},
    )


@pytest.fixture(autouse=True, scope="session")
def _register_clients(api_factory: APIClientFactory) -> None:
    api_factory.register("users", UserServiceClient)
