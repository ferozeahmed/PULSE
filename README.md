# PULSE — Playwright Uncomplicated Layered Scalable Execution

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

## Parallel execution

`pulse-tf[all]` includes `pytest-xdist`. All PULSE fixtures are
function/session-scoped with no shared mutable global state, so running
in parallel needs no extra setup:

    uv run pytest -n auto

See `examples/` for a full runnable sample suite.
