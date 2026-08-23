# PULSE Test Framework — Design Spec

**Date:** 2026-08-23
**Status:** Approved for planning

## Summary

PULSE (Playwright Uncomplicated Layered Scalable Execution) is an installable
Python package (`pulse-tf`) providing a reusable test automation foundation
for both web (Playwright) and API (httpx) testing. It ships a `BasePage` for
building page object models, a `BaseAPIClient` + factory/registry for
building API clients, shared config/logging/reporting, and a pytest plugin
that wires all of it into fixtures. Other test frameworks install it as a
dependency and extend its base classes rather than rebuilding this
foundation themselves.

## Goals

- Single package that consuming frameworks `pip`/`uv` install and extend.
- Support both web (Playwright) and API (httpx) testing, decoupled via
  optional extras so consumers only pull in what they use.
- Base classes (`BasePage`, `BaseAPIClient`) designed for subclassing —
  the page object model and API client factory patterns are the primary
  extension points.
- Pytest plugin auto-registers fixtures on install — no boilerplate wiring
  required in consuming repos beyond installing the package.
- Built-in structured logging and (optional) Allure reporting on every
  action/request, with no extra code required from consumers to get it.

## Non-Goals (v1)

- Retry/backoff logic in the API client (can be layered on later via
  `tenacity` if a consumer needs it).
- A custom locator-strategy abstraction on top of Playwright's own
  locators.
- Wrapping Playwright's own exceptions.
- Multi-package split (`pulse-core`/`pulse-web`/`pulse-api`) — a single
  package with optional extras is sufficient until there's evidence more
  decoupling is needed.

## Distribution & Tooling

- Package name: **`pulse-tf`**, importable as `pulse_tf`.
- Managed with **uv** (`pyproject.toml` + `uv.lock`).
- Published as an installable Python package (PyPI or an internal/private
  index — mechanism TBD by whoever owns publishing infra; the package
  itself is index-agnostic).
- Minimum Python version: **3.10**.
- Registered as a pytest plugin via `[project.entry-points.pytest11]`, so
  installing the package is sufficient to activate its fixtures.

### Optional extras

| Extra | Adds | Enables |
|---|---|---|
| *(core, always installed)* | `pydantic-settings`, stdlib `logging` | `pulse_settings` fixture, logging, exceptions |
| `web` | `playwright`, `pytest-playwright` | `BasePage`, config-injected browser/context fixtures, screenshot-on-failure |
| `api` | `httpx` | `BaseAPIClient`, `api_factory` fixture |
| `allure` | `allure-pytest` | Automatic Allure steps/attachments on `BasePage`/`BaseAPIClient` actions |
| `all` | all of the above + `pytest-xdist` | Full framework + parallel execution |

The plugin (`pulse_tf/plugin.py`) conditionally registers fixtures/hooks
based on which of these are importable at collection time, so a
core+`api`-only install never touches Playwright.

## Package Layout

```
pulse-tf/
├── pyproject.toml
├── src/pulse_tf/
│   ├── __init__.py
│   ├── config/
│   │   └── settings.py         # PulseSettings (pydantic-settings)
│   ├── web/
│   │   └── base_page.py        # BasePage
│   ├── api/
│   │   ├── base_client.py      # BaseAPIClient
│   │   └── factory.py          # APIClientFactory (registry)
│   ├── logging/
│   │   └── logger.py           # get_logger, log_step, redaction
│   ├── reporting/
│   │   └── allure_utils.py     # step/attach wrappers, no-op if allure absent
│   ├── plugin.py                # pytest11 entry point, conditional fixture registration
│   └── exceptions.py            # PulseConfigError, PulseAPIError
├── tests/                       # PULSE's own unit + integration tests
├── examples/                    # sample consumer suite (web + api) — living docs
└── docs/
```

## Components

### Config — `PulseSettings`

A `pydantic-settings` `BaseSettings` subclass, loaded from environment
variables / `.env`, validated eagerly (fails fast at session start rather
than mid-test). Fields:

- `environment` (dev/staging/prod)
- `base_url` — web base URL
- `api_base_urls` — `dict[str, str]`, keyed by service name, used by the
  API factory
- `browser` — chromium/firefox/webkit
- `headless` — bool
- `default_timeout`
- `allure_results_dir`
- `log_level`

**Extension pattern:** the plugin defines a `pulse_settings` fixture
(`return PulseSettings()`). Every other PULSE fixture depends on
`pulse_settings` by name. A consuming framework that needs extra fields
subclasses it (`class MySettings(PulseSettings): auth_token: str`) and
**redefines the `pulse_settings` fixture** with the same name in its own
`conftest.py`. Pytest's normal fixture-override resolution (closest
conftest wins) means every downstream PULSE fixture picks up the subclass
automatically — no registry or plugin hook needed.

### Web — `BasePage`

Wraps a Playwright `Page` (sync API) + `PulseSettings`. Core methods:
`navigate(url)`, `click(locator)`, `fill(locator, text)`,
`get_text(locator)`, `is_visible(locator)`, `wait_for(locator, state=...)`,
`screenshot(name)`. Every action:

1. Logs a structured step via `pulse_tf.logging`.
2. If the `allure` extra is installed, wraps the action in `allure.step(...)`
   automatically.

Locators are plain Playwright selector/locator strings — no custom
abstraction on top.

Built **on top of `pytest-playwright`**, not a replacement for it. PULSE
hooks into `browser_type_launch_args` / `browser_context_args` to inject
`headless`, `base_url`, and viewport settings from `PulseSettings`.
Consumers use pytest-playwright's own `page` fixture directly and pass it
into their `BasePage` subclasses:

```python
class LoginPage(BasePage):
    USERNAME = "#username"
    PASSWORD = "#password"
    SUBMIT = "button[type=submit]"

    def login(self, user: str, pwd: str) -> None:
        self.fill(self.USERNAME, user)
        self.fill(self.PASSWORD, pwd)
        self.click(self.SUBMIT)

def test_login(page, pulse_settings):
    LoginPage(page, pulse_settings).login("user", "pass")
```

**Screenshot-on-failure:** the plugin implements
`pytest_runtest_makereport`, capturing a screenshot from the active `page`
fixture on test failure and attaching it to the Allure report. Active only
when both `web` and `allure` extras are installed.

### API — `BaseAPIClient` + `APIClientFactory`

Wraps an `httpx.Client` + `PulseSettings`. Methods: `get/post/put/patch/delete`.
Each call logs request/response (headers/body), redacting configured
sensitive fields (default redaction list includes `Authorization`,
`password`). Raises `PulseAPIError` (status + response body attached) on
non-2xx responses by default; overridable per-call via
`raise_for_status=False`.

```python
class UserServiceClient(BaseAPIClient):
    def get_user(self, user_id: str):
        return self.get(f"/users/{user_id}")
```

`APIClientFactory`, exposed as the `api_factory` fixture (registered only
when the `api` extra is installed):

```python
api_factory.register("users", UserServiceClient)   # conftest.py
client = api_factory.create("users")                 # test — wires base_url from
                                                       # pulse_settings.api_base_urls["users"]
```

The `api_factory` fixture is session-scoped (one registry per test-session,
per xdist worker process). The factory resolves each service's `base_url`
from `pulse_settings.api_base_urls[name]` and caches one client instance
per service name for the life of the session, so repeated `create()`
calls for the same service reuse the same `httpx.Client` (and its
connection pool) rather than opening a new one per test.

No retry/backoff in v1 (see Non-Goals).

### Logging & Reporting

- `pulse_tf.logging.get_logger(name)` — standard-library logger, consistent
  formatter across the framework.
- `pulse_tf.logging.log_step(message)` — used internally by `BasePage` and
  `BaseAPIClient`; also callable directly by consumers for custom steps.
- Redaction: a configurable list of header/field names scrubbed from log
  output and Allure attachments (default covers common secret fields).
- `pulse_tf.reporting.allure_utils` wraps `allure.step`/`allure.attach`
  behind a guarded import — becomes a no-op if `allure-pytest` isn't
  installed, so `BasePage`/`BaseAPIClient` behave identically either way.

### Error Handling

- `PulseConfigError` — settings validation failures, raised at session
  start (fail fast).
- `PulseAPIError` — non-2xx API responses; carries status code and
  response body for debugging.
- Playwright's own exceptions (e.g. `TimeoutError`) are **not** wrapped —
  they surface as-is.

### Parallel Execution

No custom code required. All PULSE fixtures are function/session-scoped
with no shared mutable global state, so `pytest-xdist` (included in the
`all` extra) works out of the box. Usage (`-n auto`) is documented, not
implemented.

## Testing PULSE Itself

- **Unit tests**: config loading + env var overrides, `api_factory`
  registration/creation, log redaction logic. No browser or network.
- **API integration tests**: `BaseAPIClient` against a local mock (e.g.
  `respx` for httpx mocking) — no real network calls in CI.
- **Web integration tests**: `BasePage` against a small local static HTML
  fixture page, proving the pytest-playwright hook wiring (config
  injection) and screenshot-on-failure work end-to-end.
- **`examples/`**: a small runnable sample suite (one web PageObject, one
  API client) that doubles as living documentation of the extension
  patterns and is run in CI as a smoke test of the real developer
  experience.

## CI

GitHub Actions: lint (`ruff`), type-check (`mypy`), run unit + integration
tests across Python 3.10/3.11/3.12, build the package (`uv build`).

## Open Questions (deferred, not blocking v1)

- Which package index (PyPI public vs. private/internal registry) —
  decided by whoever owns publishing infrastructure; doesn't affect the
  package's design.
- Retry/backoff strategy for `BaseAPIClient`, if/when a consumer needs it.
