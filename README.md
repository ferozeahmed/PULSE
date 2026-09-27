# PULSE — Playwright Uncomplicated Layered Scalable Execution - Python

A base test automation framework for building web (Playwright) and API
(httpx) test suites, distributed as an installable Python package that
other frameworks extend.

## Install

    uv add "pulse-tf[all]"    # web + api + allure + xdist
    uv add "pulse-tf[web]"    # web only
    uv add "pulse-tf[api]"    # api only

## Quickstart — API testing

    from pulse_tf.api.base_client import BaseAPIClient

    class UserServiceClient(BaseAPIClient):
        def get_user(self, user_id):
            return self.get(f"/users/{user_id}").json()

Register it once, e.g. in your `conftest.py`:

    @pytest.fixture(autouse=True, scope="session")
    def _register_clients(api_factory):
        api_factory.register("users", UserServiceClient)

Configure `PULSE_API_BASE_URLS='{"users": "https://api.example.com"}'`
(or override the `pulse_settings` fixture — see below), then in a test:

    def test_get_user(api_factory):
        client = api_factory.create("users")
        assert client.get_user("1")["id"] == 1

## Quickstart — Web testing

    from pulse_tf.web.base_page import BasePage

    class LoginPage(BasePage):
        USERNAME = "#username"
        PASSWORD = "#password"
        SUBMIT = "#submit"

        def login(self, user, pwd):
            self.fill(self.USERNAME, user)
            self.fill(self.PASSWORD, pwd)
            self.click(self.SUBMIT)

    def test_login(page, pulse_settings):
        LoginPage(page, pulse_settings).login("bob", "secret")

Set `PULSE_BASE_URL` (or override `pulse_settings`) to point at your app.

## Extending settings

    from pulse_tf.config.settings import PulseSettings

    class MySettings(PulseSettings):
        auth_token: str

    @pytest.fixture(scope="session")
    def pulse_settings():
        return MySettings()

Every PULSE fixture depends on `pulse_settings` by name, so overriding it
in your own `conftest.py` (pytest's standard fixture-override rule: the
closest conftest wins) flows through automatically.

## Running differently-configured suites: separate invocations

`pulse_settings` (and everything that depends on it — `api_factory`, the
browser fixtures in `pulse_tf.web.fixtures`) is a **session-scoped**
fixture, and pytest caches a session-scoped fixture's resolved value once
per `FixtureDef` object for the life of the process — not per subtree, and
not keyed by which `conftest.py` override produced it. So a single pytest
process can only cleanly support **one** resolved `pulse_settings`
configuration. If two subtrees of your test suite each override
`pulse_settings` with genuinely different values (a different `base_url`,
different `api_base_urls`, etc.), whichever subtree's override resolves
first "wins" for the rest of that process, silently poisoning the fixture
value for every other subtree that runs afterward in the same run.

This project's own `tests/` (library unit tests) and `examples/` (a
runnable sample suite, with its own `base_url`/`api_base_urls`) are exactly
such a case, so this repo's own CI (see `.github/workflows/ci.yml`) runs
them as two separate invocations rather than one combined collection:

    uv run pytest tests/
    uv run pytest examples/

If your own test suite has subtrees that genuinely need different
`pulse_settings` configurations, follow the same pattern — one `uv run
pytest <path>` invocation per configuration — rather than defining
different `pulse_settings` overrides in sub-`conftest.py` files and
expecting them to coexist in one run; that's the pattern the fixture-caching
behavior above rules out.

## Parallel execution

`pulse-tf[all]` includes `pytest-xdist`. All PULSE fixtures are
function/session-scoped with no shared mutable global state, so running
in parallel needs no extra setup:

    uv run pytest -n auto

See `examples/` for a full runnable sample suite.
