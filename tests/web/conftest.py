import http.server
import threading
from pathlib import Path

import pytest

from pulse_tf.config.settings import PulseSettings

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def static_server_url():
    def handler(*args, **kwargs):
        return http.server.SimpleHTTPRequestHandler(*args, directory=str(FIXTURES_DIR), **kwargs)

    server = http.server.ThreadingHTTPServer(("localhost", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://{server.server_address[0]}:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture(scope="session")
def pulse_settings(static_server_url):
    # headless is passed explicitly (even though True is also the default) so
    # that it lands in model_fields_set and this suite exercises the
    # "explicitly configured" override path of
    # pulse_tf.web.fixtures.browser_type_launch_args.
    return PulseSettings(base_url=static_server_url, headless=True)
