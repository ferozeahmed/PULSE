import http.server
import threading
from pathlib import Path

import pytest

from pulse_tf.config.settings import PulseSettings

FIXTURES_DIR = Path(__file__).parent / "fixtures"


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
    return PulseSettings(base_url=f"http://{host}:{port}")
