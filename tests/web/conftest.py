import http.server
import threading
from pathlib import Path

import pytest

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
