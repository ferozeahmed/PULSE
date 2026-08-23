# PULSE Test Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `pulse-tf`, an installable Python package providing base classes (`BasePage`, `BaseAPIClient`), a factory/registry for API clients, shared config/logging/reporting, and a pytest plugin — so other test frameworks can install it and extend it instead of rebuilding this foundation.

**Architecture:** A single package with a core (always installed) plus three optional extras (`web`, `api`, `allure`) whose fixtures the pytest plugin (`pulse_tf/plugin.py`) registers conditionally based on what's importable. Web capability builds on top of `pytest-playwright` (config injection via fixture override) rather than reimplementing browser lifecycle. API capability is a thin `httpx`-based client + a session-scoped registry/factory.

**Tech Stack:** Python 3.10+, uv, pydantic-settings, pytest, playwright + pytest-playwright, httpx, allure-pytest, ruff, mypy, respx (test-only).

**Spec:** `docs/superpowers/specs/2026-08-23-pulse-test-framework-design.md`

## Global Constraints

- Minimum Python version: 3.10 (from spec's Distribution & Tooling).
- Package/import name: `pulse-tf` / `pulse_tf` (from spec).
- Dependency/build tooling: uv + `pyproject.toml` (from spec).
- Optional extras exactly as specified: `web`, `api`, `allure`, `all` (from spec's Optional Extras table).
- No retry/backoff logic in `BaseAPIClient` (spec Non-Goals).
- No custom locator-strategy abstraction on top of Playwright's own locators (spec Non-Goals).
- Playwright's own exceptions are never wrapped (spec Non-Goals / Error Handling).
- Default redaction covers `Authorization`, `password`, `token`, `api_key`, `secret` header/field names (spec Logging & Reporting section, generalized from spec's example list).
- `pulse_settings` fixture is session-scoped; `api_factory` fixture is session-scoped with per-service instance caching (spec Config / API sections).

---

## File Structure

```
pulse-tf/
├── pyproject.toml
├── README.md
├── .gitignore
├── .github/workflows/ci.yml
├── src/pulse_tf/
│   ├── __init__.py
│   ├── exceptions.py            # PulseConfigError, PulseAPIError
│   ├── plugin.py                # pytest11 entry point — conditional fixture registration
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py          # PulseSettings, load_settings(), pulse_settings fixture
│   ├── logging/
│   │   ├── __init__.py
│   │   └── logger.py            # get_logger, redact, log_step
│   ├── reporting/
│   │   ├── __init__.py
│   │   └── allure_utils.py      # step(), attach_screenshot(), attach_text() — no-op if allure absent
│   ├── api/
│   │   ├── __init__.py
│   │   ├── base_client.py       # BaseAPIClient
│   │   └── factory.py           # APIClientFactory, api_factory fixture
│   └── web/
│       ├── __init__.py
│       ├── base_page.py         # BasePage
│       └── fixtures.py          # browser_type_launch_args / browser_context_args overrides
├── tests/
│   ├── conftest.py               # enables pytester plugin
│   ├── test_package.py
│   ├── test_settings.py
│   ├── test_logging.py
│   ├── test_allure_utils.py
│   ├── api/
│   │   ├── test_base_client.py
│   │   └── test_factory.py
│   └── web/
│       ├── conftest.py           # static_server_url, pulse_settings (task 8)
│       ├── fixtures/index.html
│       ├── test_base_page.py
│       ├── test_fixtures.py
│       └── test_screenshot_on_failure.py
└── examples/
    ├── __init__.py
    ├── conftest.py
    ├── api/
    │   ├── __init__.py
    │   ├── clients/__init__.py
    │   ├── clients/user_client.py
    │   └── test_users.py
    └── web/
        ├── __init__.py
        ├── conftest.py
        ├── fixtures/index.html
        ├── pages/__init__.py
        ├── pages/login_page.py
        └── test_login.py
```

---

### Task 1: Project scaffolding & packaging

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `src/pulse_tf/__init__.py`
- Create: `src/pulse_tf/exceptions.py`
- Create: `src/pulse_tf/plugin.py`
- Test: `tests/test_package.py`

**Interfaces:**
- Produces: `pulse_tf.__version__: str`; `pulse_tf.exceptions.PulseConfigError(Exception)`; `pulse_tf.exceptions.PulseAPIError(Exception)` with `__init__(self, message: str, *, status_code: int, response_body: str)` and attributes `.status_code`, `.response_body`.

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "pulse-tf"
version = "0.1.0"
description = "Playwright Uncomplicated Layered Scalable Execution — a base test automation framework for web and API testing."
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
dependencies = [
    "pydantic-settings>=2.4",
]

[project.optional-dependencies]
web = ["playwright>=1.45", "pytest-playwright>=0.5"]
api = ["httpx>=0.27"]
allure = ["allure-pytest>=2.13"]
all = ["pulse-tf[web,api,allure]", "pytest-xdist>=3.6"]

[project.entry-points.pytest11]
pulse_tf = "pulse_tf.plugin"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/pulse_tf"]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.6",
    "mypy>=1.11",
    "respx>=0.21",
]

[tool.pytest.ini_options]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.mypy]
python_version = "3.10"
packages = ["pulse_tf"]
strict = true
```

- [ ] **Step 2: Create `.gitignore`**

```
__pycache__/
*.pyc
.venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
allure-results/
dist/
*.egg-info/
.env
```

- [ ] **Step 3: Create `src/pulse_tf/__init__.py`**

```python
__version__ = "0.1.0"
```

- [ ] **Step 4: Create `src/pulse_tf/exceptions.py`**

```python
from __future__ import annotations


class PulseConfigError(Exception):
    """Raised when PulseSettings fails validation, or an API client factory
    lookup can't be resolved."""


class PulseAPIError(Exception):
    def __init__(self, message: str, *, status_code: int, response_body: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
```

- [ ] **Step 5: Create empty `src/pulse_tf/plugin.py`**

```python
"""pytest11 entry point for pulse-tf. Fixtures are registered here by
later tasks, conditionally based on which optional extras are installed."""
```

- [ ] **Step 6: Install the package in editable mode with all extras**

Run: `uv sync --all-extras`
Expected: resolves and installs successfully (no browsers needed yet — that's step 8 in Task 7).

- [ ] **Step 7: Write `tests/test_package.py`**

```python
import pulse_tf
from pulse_tf.exceptions import PulseAPIError, PulseConfigError


def test_version_is_a_string():
    assert isinstance(pulse_tf.__version__, str)


def test_pulse_config_error_is_an_exception():
    assert issubclass(PulseConfigError, Exception)


def test_pulse_api_error_carries_status_and_body():
    err = PulseAPIError("boom", status_code=500, response_body="oops")
    assert err.status_code == 500
    assert err.response_body == "oops"
    assert str(err) == "boom"
```

- [ ] **Step 8: Run the test and verify it passes**

Run: `uv run pytest tests/test_package.py -v`
Expected: 3 passed

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml .gitignore src/pulse_tf/__init__.py src/pulse_tf/exceptions.py src/pulse_tf/plugin.py tests/test_package.py
git commit -m "chore: scaffold pulse-tf package with exceptions module"
```

---

### Task 2: Config — `PulseSettings` and the `pulse_settings` fixture

**Files:**
- Create: `src/pulse_tf/config/__init__.py`
- Create: `src/pulse_tf/config/settings.py`
- Modify: `src/pulse_tf/plugin.py`
- Test: `tests/test_settings.py`

**Interfaces:**
- Consumes: `PulseConfigError` from `pulse_tf.exceptions` (Task 1).
- Produces: `PulseSettings(BaseSettings)` with fields `environment: Literal["dev","staging","prod"]`, `base_url: str`, `api_base_urls: dict[str, str]`, `browser: Literal["chromium","firefox","webkit"]`, `headless: bool`, `default_timeout: int`, `allure_results_dir: str`, `log_level: str`; `load_settings(settings_cls: type[PulseSettings] = PulseSettings) -> PulseSettings`; pytest fixture `pulse_settings() -> PulseSettings` (session-scoped), registered via `plugin.py`.

- [ ] **Step 1: Write the failing tests in `tests/test_settings.py`**

```python
import pytest

from pulse_tf.config.settings import PulseSettings, load_settings
from pulse_tf.exceptions import PulseConfigError


def test_defaults_load_without_env_vars(monkeypatch):
    monkeypatch.delenv("PULSE_BASE_URL", raising=False)
    settings = load_settings()
    assert settings.environment == "dev"
    assert settings.browser == "chromium"
    assert settings.headless is True
    assert settings.api_base_urls == {}


def test_env_var_overrides_default(monkeypatch):
    monkeypatch.setenv("PULSE_BASE_URL", "https://example.test")
    monkeypatch.setenv("PULSE_HEADLESS", "false")
    settings = load_settings()
    assert settings.base_url == "https://example.test"
    assert settings.headless is False


def test_invalid_browser_raises_pulse_config_error(monkeypatch):
    monkeypatch.setenv("PULSE_BROWSER", "not-a-browser")
    with pytest.raises(PulseConfigError):
        load_settings()
    monkeypatch.delenv("PULSE_BROWSER", raising=False)


def test_subclass_adds_fields(monkeypatch):
    monkeypatch.setenv("PULSE_AUTH_TOKEN", "secret123")

    class MySettings(PulseSettings):
        auth_token: str

    settings = load_settings(MySettings)
    assert settings.auth_token == "secret123"
    monkeypatch.delenv("PULSE_AUTH_TOKEN", raising=False)


def test_pulse_settings_fixture_is_available(pulse_settings):
    assert isinstance(pulse_settings, PulseSettings)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_settings.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pulse_tf.config'`

- [ ] **Step 3: Create `src/pulse_tf/config/__init__.py`** (empty file)

- [ ] **Step 4: Create `src/pulse_tf/config/settings.py`**

```python
from __future__ import annotations

from typing import Literal

import pytest
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from pulse_tf.exceptions import PulseConfigError


class PulseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PULSE_", env_file=".env", extra="ignore")

    environment: Literal["dev", "staging", "prod"] = "dev"
    base_url: str = "http://localhost"
    api_base_urls: dict[str, str] = {}
    browser: Literal["chromium", "firefox", "webkit"] = "chromium"
    headless: bool = True
    default_timeout: int = 30000
    allure_results_dir: str = "allure-results"
    log_level: str = "INFO"


def load_settings(settings_cls: type[PulseSettings] = PulseSettings) -> PulseSettings:
    try:
        return settings_cls()
    except ValidationError as exc:
        raise PulseConfigError(str(exc)) from exc


@pytest.fixture(scope="session")
def pulse_settings() -> PulseSettings:
    return load_settings()
```

- [ ] **Step 5: Register the fixture in `src/pulse_tf/plugin.py`**

```python
"""pytest11 entry point for pulse-tf. Fixtures are registered here,
conditionally based on which optional extras are installed."""

from pulse_tf.config.settings import pulse_settings  # noqa: F401
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_settings.py -v`
Expected: 5 passed

- [ ] **Step 7: Commit**

```bash
git add src/pulse_tf/config src/pulse_tf/plugin.py tests/test_settings.py
git commit -m "feat: add PulseSettings and pulse_settings fixture"
```

---

### Task 3: Logging — `get_logger`, `redact`, `log_step`

**Files:**
- Create: `src/pulse_tf/logging/__init__.py`
- Create: `src/pulse_tf/logging/logger.py`
- Test: `tests/test_logging.py`

**Interfaces:**
- Produces: `get_logger(name: str) -> logging.Logger`; `redact(data: dict[str, str], *, redacted_keys: set[str] = DEFAULT_REDACTED_KEYS) -> dict[str, str]`; `DEFAULT_REDACTED_KEYS: set[str]` (`{"authorization", "password", "token", "api_key", "secret"}`); `log_step(message: str, *, logger_name: str = "pulse_tf") -> None`.

- [ ] **Step 1: Write the failing tests in `tests/test_logging.py`**

```python
import logging

from pulse_tf.logging.logger import get_logger, log_step, redact


def test_get_logger_returns_configured_logger():
    logger = get_logger("pulse_tf.test")
    assert logger.name == "pulse_tf.test"
    assert len(logger.handlers) == 1


def test_get_logger_does_not_duplicate_handlers():
    logger1 = get_logger("pulse_tf.test_dup")
    logger2 = get_logger("pulse_tf.test_dup")
    assert logger1 is logger2
    assert len(logger1.handlers) == 1


def test_redact_masks_default_sensitive_keys():
    data = {"Authorization": "Bearer abc", "username": "bob"}
    result = redact(data)
    assert result["Authorization"] == "***REDACTED***"
    assert result["username"] == "bob"


def test_redact_is_case_insensitive():
    data = {"PASSWORD": "hunter2"}
    assert redact(data)["PASSWORD"] == "***REDACTED***"


def test_log_step_writes_info_log(caplog):
    with caplog.at_level(logging.INFO, logger="pulse_tf"):
        log_step("clicked login button")
    assert "clicked login button" in caplog.text
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_logging.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pulse_tf.logging'`

- [ ] **Step 3: Create `src/pulse_tf/logging/__init__.py`** (empty file)

- [ ] **Step 4: Create `src/pulse_tf/logging/logger.py`**

```python
from __future__ import annotations

import logging

DEFAULT_REDACTED_KEYS = {"authorization", "password", "token", "api_key", "secret"}


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def redact(
    data: dict[str, str], *, redacted_keys: set[str] = DEFAULT_REDACTED_KEYS
) -> dict[str, str]:
    return {
        key: ("***REDACTED***" if key.lower() in redacted_keys else value)
        for key, value in data.items()
    }


def log_step(message: str, *, logger_name: str = "pulse_tf") -> None:
    get_logger(logger_name).info(message)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_logging.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add src/pulse_tf/logging tests/test_logging.py
git commit -m "feat: add logging module with redaction"
```

---

### Task 4: Reporting — `allure_utils`

**Files:**
- Create: `src/pulse_tf/reporting/__init__.py`
- Create: `src/pulse_tf/reporting/allure_utils.py`
- Test: `tests/test_allure_utils.py`

**Interfaces:**
- Produces: `HAS_ALLURE: bool`; `step(name: str) -> contextmanager` (no-op if `HAS_ALLURE` is `False`); `attach_screenshot(data: bytes, name: str = "screenshot") -> None`; `attach_text(data: str, name: str = "log") -> None`.

- [ ] **Step 1: Write the failing tests in `tests/test_allure_utils.py`**

```python
from contextlib import nullcontext

from pulse_tf.reporting import allure_utils


def test_step_is_noop_without_allure(monkeypatch):
    monkeypatch.setattr(allure_utils, "HAS_ALLURE", False)
    with allure_utils.step("do a thing"):
        pass  # must not raise


def test_attach_screenshot_is_noop_without_allure(monkeypatch):
    monkeypatch.setattr(allure_utils, "HAS_ALLURE", False)
    allure_utils.attach_screenshot(b"fake-png-bytes")  # must not raise


def test_step_wraps_allure_step_when_available(monkeypatch):
    calls = []

    class FakeAllure:
        class attachment_type:
            PNG = "png"
            TEXT = "text"

        @staticmethod
        def step(name):
            calls.append(name)
            return nullcontext()

        @staticmethod
        def attach(data, name, attachment_type):
            calls.append((data, name, attachment_type))

    monkeypatch.setattr(allure_utils, "HAS_ALLURE", True)
    monkeypatch.setattr(allure_utils, "allure", FakeAllure)

    with allure_utils.step("clicked button"):
        pass

    assert calls == ["clicked button"]


def test_attach_screenshot_calls_allure_attach_when_available(monkeypatch):
    calls = []

    class FakeAllure:
        class attachment_type:
            PNG = "png"
            TEXT = "text"

        @staticmethod
        def attach(data, name, attachment_type):
            calls.append((data, name, attachment_type))

    monkeypatch.setattr(allure_utils, "HAS_ALLURE", True)
    monkeypatch.setattr(allure_utils, "allure", FakeAllure)

    allure_utils.attach_screenshot(b"bytes", name="shot")

    assert calls == [(b"bytes", "shot", "png")]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_allure_utils.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pulse_tf.reporting'`

- [ ] **Step 3: Create `src/pulse_tf/reporting/__init__.py`** (empty file)

- [ ] **Step 4: Create `src/pulse_tf/reporting/allure_utils.py`**

```python
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

try:
    import allure

    HAS_ALLURE = True
except ImportError:
    HAS_ALLURE = False


@contextmanager
def step(name: str) -> Iterator[None]:
    if HAS_ALLURE:
        with allure.step(name):
            yield
    else:
        yield


def attach_screenshot(data: bytes, name: str = "screenshot") -> None:
    if HAS_ALLURE:
        allure.attach(data, name=name, attachment_type=allure.attachment_type.PNG)


def attach_text(data: str, name: str = "log") -> None:
    if HAS_ALLURE:
        allure.attach(data, name=name, attachment_type=allure.attachment_type.TEXT)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_allure_utils.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add src/pulse_tf/reporting tests/test_allure_utils.py
git commit -m "feat: add allure_utils reporting wrapper (no-op without allure)"
```

---

### Task 5: API — `BaseAPIClient`

**Files:**
- Create: `src/pulse_tf/api/__init__.py`
- Create: `src/pulse_tf/api/base_client.py`
- Test: `tests/api/test_base_client.py`
- Create: `tests/api/__init__.py` (empty file, so `tests/api` is a package)

**Interfaces:**
- Consumes: `PulseAPIError` (Task 1); `get_logger`, `redact` (Task 3); `allure_utils.step` (Task 4).
- Produces: `BaseAPIClient(base_url: str, *, client: httpx.Client | None = None)` with methods `get/post/put/patch/delete(path: str, *, raise_for_status: bool = True, **kwargs) -> httpx.Response`, raising `PulseAPIError` on non-2xx when `raise_for_status=True`; attribute `.base_url: str`.

- [ ] **Step 1: Write the failing tests in `tests/api/test_base_client.py`**

```python
import json
import logging

import httpx
import pytest
import respx

from pulse_tf.api.base_client import BaseAPIClient
from pulse_tf.exceptions import PulseAPIError


@pytest.fixture
def client():
    return BaseAPIClient("https://api.test")


@respx.mock
def test_get_returns_response(client):
    respx.get("https://api.test/users/1").mock(return_value=httpx.Response(200, json={"id": 1}))
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json() == {"id": 1}


@respx.mock
def test_non_2xx_raises_pulse_api_error_by_default(client):
    respx.get("https://api.test/users/99").mock(return_value=httpx.Response(404, text="not found"))
    with pytest.raises(PulseAPIError) as exc_info:
        client.get("/users/99")
    assert exc_info.value.status_code == 404
    assert exc_info.value.response_body == "not found"


@respx.mock
def test_raise_for_status_false_returns_error_response(client):
    respx.get("https://api.test/users/99").mock(return_value=httpx.Response(404, text="not found"))
    response = client.get("/users/99", raise_for_status=False)
    assert response.status_code == 404


@respx.mock
def test_post_sends_json_body(client):
    route = respx.post("https://api.test/users").mock(return_value=httpx.Response(201, json={"id": 2}))
    response = client.post("/users", json={"name": "bob"})
    assert response.status_code == 201
    assert route.called
    assert json.loads(route.calls.last.request.content) == {"name": "bob"}


def test_authorization_header_is_redacted_in_logs(client, caplog):
    with respx.mock:
        respx.get("https://api.test/secret").mock(return_value=httpx.Response(200))
        with caplog.at_level(logging.INFO, logger="pulse_tf.api"):
            client.get("/secret", headers={"Authorization": "Bearer topsecret"})
    assert "topsecret" not in caplog.text
    assert "REDACTED" in caplog.text
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/api/test_base_client.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pulse_tf.api'`

- [ ] **Step 3: Create `src/pulse_tf/api/__init__.py`** and `tests/api/__init__.py`** (empty files)

- [ ] **Step 4: Create `src/pulse_tf/api/base_client.py`**

```python
from __future__ import annotations

from typing import Any

import httpx

from pulse_tf.exceptions import PulseAPIError
from pulse_tf.logging.logger import get_logger, redact
from pulse_tf.reporting import allure_utils

_logger = get_logger("pulse_tf.api")


class BaseAPIClient:
    def __init__(self, base_url: str, *, client: httpx.Client | None = None) -> None:
        self.base_url = base_url
        self._client = client or httpx.Client(base_url=base_url)

    def get(self, path: str, *, raise_for_status: bool = True, **kwargs: Any) -> httpx.Response:
        return self._request("GET", path, raise_for_status=raise_for_status, **kwargs)

    def post(self, path: str, *, raise_for_status: bool = True, **kwargs: Any) -> httpx.Response:
        return self._request("POST", path, raise_for_status=raise_for_status, **kwargs)

    def put(self, path: str, *, raise_for_status: bool = True, **kwargs: Any) -> httpx.Response:
        return self._request("PUT", path, raise_for_status=raise_for_status, **kwargs)

    def patch(self, path: str, *, raise_for_status: bool = True, **kwargs: Any) -> httpx.Response:
        return self._request("PATCH", path, raise_for_status=raise_for_status, **kwargs)

    def delete(self, path: str, *, raise_for_status: bool = True, **kwargs: Any) -> httpx.Response:
        return self._request("DELETE", path, raise_for_status=raise_for_status, **kwargs)

    def _request(
        self, method: str, path: str, *, raise_for_status: bool, **kwargs: Any
    ) -> httpx.Response:
        step_name = f"{method} {self.base_url}{path}"
        with allure_utils.step(step_name):
            _logger.info(
                "%s request headers=%s", step_name, redact(dict(kwargs.get("headers") or {}))
            )
            response = self._client.request(method, path, **kwargs)
            _logger.info("%s -> %s", step_name, response.status_code)
            if raise_for_status and response.is_error:
                raise PulseAPIError(
                    f"{step_name} returned {response.status_code}",
                    status_code=response.status_code,
                    response_body=response.text,
                )
            return response
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/api/test_base_client.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add src/pulse_tf/api/__init__.py src/pulse_tf/api/base_client.py tests/api
git commit -m "feat: add BaseAPIClient with logging, redaction, and PulseAPIError"
```

---

### Task 6: API — `APIClientFactory` and the `api_factory` fixture

**Files:**
- Create: `src/pulse_tf/api/factory.py`
- Modify: `src/pulse_tf/plugin.py`
- Test: `tests/api/test_factory.py`

**Interfaces:**
- Consumes: `BaseAPIClient` (Task 5); `PulseSettings` (Task 2); `PulseConfigError` (Task 1).
- Produces: `APIClientFactory(settings: PulseSettings)` with `.register(name: str, client_cls: type[BaseAPIClient]) -> None` and `.create(name: str) -> BaseAPIClient` (caches per service name; raises `PulseConfigError` if unregistered or missing `base_url`); pytest fixture `api_factory(pulse_settings) -> APIClientFactory` (session-scoped), registered via `plugin.py` only when `httpx` is importable.

- [ ] **Step 1: Write the failing tests in `tests/api/test_factory.py`**

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/api/test_factory.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pulse_tf.api.factory'`

- [ ] **Step 3: Create `src/pulse_tf/api/factory.py`**

```python
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
```

- [ ] **Step 4: Register the fixture conditionally in `src/pulse_tf/plugin.py`**

```python
"""pytest11 entry point for pulse-tf. Fixtures are registered here,
conditionally based on which optional extras are installed."""

from pulse_tf.config.settings import pulse_settings  # noqa: F401

try:
    import httpx  # noqa: F401
except ImportError:
    pass
else:
    from pulse_tf.api.factory import api_factory  # noqa: F401
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/api/test_factory.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add src/pulse_tf/api/factory.py src/pulse_tf/plugin.py tests/api/test_factory.py
git commit -m "feat: add APIClientFactory and api_factory fixture"
```

---

### Task 7: Web — `BasePage`

**Files:**
- Create: `src/pulse_tf/web/__init__.py`
- Create: `src/pulse_tf/web/base_page.py`
- Create: `tests/web/__init__.py`, `tests/web/conftest.py`, `tests/web/fixtures/index.html`
- Test: `tests/web/test_base_page.py`

**Interfaces:**
- Consumes: `get_logger` (Task 3); `allure_utils.step`, `allure_utils.attach_screenshot` (Task 4); `PulseSettings` (Task 2, type only).
- Produces: `BasePage(page: playwright.sync_api.Page, settings: PulseSettings | None = None)` with `.navigate(url)`, `.click(locator)`, `.fill(locator, text)`, `.get_text(locator) -> str`, `.is_visible(locator) -> bool`, `.wait_for(locator, *, state="visible")`, `.screenshot(name="screenshot") -> bytes`.
- Also produces test fixture `static_server_url` (session-scoped, in `tests/web/conftest.py`) — reused and extended by Task 8.

- [ ] **Step 1: Install Playwright's browser binary (one-time, local dev requirement)**

Run: `uv run playwright install --with-deps chromium`
Expected: downloads and installs the chromium browser used by all web tests in this plan.

- [ ] **Step 2: Create `tests/web/fixtures/index.html`**

```html
<!DOCTYPE html>
<html>
<body>
  <input id="username" />
  <input id="password" type="password" />
  <button id="submit">Login</button>
  <p id="greeting" style="display:none">Welcome!</p>
  <script>
    document.getElementById('submit').addEventListener('click', function () {
      document.getElementById('greeting').style.display = 'block';
    });
  </script>
</body>
</html>
```

- [ ] **Step 3: Create `tests/web/__init__.py`** (empty file)

- [ ] **Step 4: Create `tests/web/conftest.py`**

```python
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
```

- [ ] **Step 5: Write the failing tests in `tests/web/test_base_page.py`**

```python
from pulse_tf.web.base_page import BasePage


def test_navigate_and_interact(page, static_server_url):
    pg = BasePage(page)
    pg.navigate(f"{static_server_url}/index.html")
    pg.fill("#username", "bob")
    pg.fill("#password", "secret")
    assert pg.is_visible("#greeting") is False
    pg.click("#submit")
    pg.wait_for("#greeting")
    assert pg.is_visible("#greeting") is True


def test_get_text_reads_element(page, static_server_url):
    pg = BasePage(page)
    pg.navigate(f"{static_server_url}/index.html")
    pg.click("#submit")
    assert pg.get_text("#greeting") == "Welcome!"
```

- [ ] **Step 6: Run the tests to verify they fail**

Run: `uv run pytest tests/web/test_base_page.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'pulse_tf.web'`

- [ ] **Step 7: Create `src/pulse_tf/web/__init__.py`** (empty file)

- [ ] **Step 8: Create `src/pulse_tf/web/base_page.py`**

```python
from __future__ import annotations

from playwright.sync_api import Page

from pulse_tf.config.settings import PulseSettings
from pulse_tf.logging.logger import get_logger
from pulse_tf.reporting import allure_utils

_logger = get_logger("pulse_tf.web")


class BasePage:
    def __init__(self, page: Page, settings: PulseSettings | None = None) -> None:
        self.page = page
        self.settings = settings

    def navigate(self, url: str) -> None:
        with allure_utils.step(f"Navigate to {url}"):
            _logger.info("navigate: %s", url)
            self.page.goto(url)

    def click(self, locator: str) -> None:
        with allure_utils.step(f"Click {locator}"):
            _logger.info("click: %s", locator)
            self.page.locator(locator).click()

    def fill(self, locator: str, text: str) -> None:
        with allure_utils.step(f"Fill {locator}"):
            _logger.info("fill: %s", locator)
            self.page.locator(locator).fill(text)

    def get_text(self, locator: str) -> str:
        with allure_utils.step(f"Get text {locator}"):
            return self.page.locator(locator).inner_text()

    def is_visible(self, locator: str) -> bool:
        return self.page.locator(locator).is_visible()

    def wait_for(self, locator: str, *, state: str = "visible") -> None:
        with allure_utils.step(f"Wait for {locator} ({state})"):
            self.page.locator(locator).wait_for(state=state)

    def screenshot(self, name: str = "screenshot") -> bytes:
        data = self.page.screenshot()
        allure_utils.attach_screenshot(data, name=name)
        return data
```

- [ ] **Step 9: Run the tests to verify they pass**

Run: `uv run pytest tests/web/test_base_page.py -v`
Expected: 2 passed

- [ ] **Step 10: Commit**

```bash
git add src/pulse_tf/web/__init__.py src/pulse_tf/web/base_page.py tests/web
git commit -m "feat: add BasePage"
```

---

### Task 8: Web — config-injected fixtures (`browser_type_launch_args`, `browser_context_args`)

**Files:**
- Create: `src/pulse_tf/web/fixtures.py`
- Modify: `src/pulse_tf/plugin.py`
- Modify: `tests/web/conftest.py` (add `pulse_settings` override for the web test subtree)
- Test: `tests/web/test_fixtures.py`

**Interfaces:**
- Consumes: `PulseSettings` (Task 2); pytest-playwright's own `browser_type_launch_args`/`browser_context_args` fixtures (overridden by same name).
- Produces: fixture overrides `browser_type_launch_args(browser_type_launch_args, pulse_settings) -> dict` (merges in `headless`); `browser_context_args(browser_context_args, pulse_settings) -> dict` (merges in `base_url`) — registered via `plugin.py` only when `playwright` is importable.

- [ ] **Step 1: Extend `tests/web/conftest.py` to point `pulse_settings` at the local static server**

Add to the bottom of the existing file:

```python
from pulse_tf.config.settings import PulseSettings


@pytest.fixture(scope="session")
def pulse_settings(static_server_url):
    return PulseSettings(base_url=static_server_url)
```

- [ ] **Step 2: Write the failing tests in `tests/web/test_fixtures.py`**

```python
from pulse_tf.web.base_page import BasePage


def test_browser_context_args_includes_base_url(browser_context_args, pulse_settings):
    assert browser_context_args["base_url"] == pulse_settings.base_url


def test_browser_type_launch_args_includes_headless(browser_type_launch_args, pulse_settings):
    assert browser_type_launch_args["headless"] == pulse_settings.headless


def test_relative_navigate_resolves_against_base_url(page, pulse_settings):
    pg = BasePage(page, pulse_settings)
    pg.navigate("/index.html")
    assert pg.is_visible("#username") is True
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/web/test_fixtures.py -v`
Expected: FAIL — `browser_context_args["base_url"]` and `browser_type_launch_args["headless"]` are absent (pulse-tf isn't merging them in yet); the relative-navigate test fails to load the page.

- [ ] **Step 4: Create `src/pulse_tf/web/fixtures.py`**

```python
from __future__ import annotations

import pytest

from pulse_tf.config.settings import PulseSettings


@pytest.fixture(scope="session")
def browser_type_launch_args(
    browser_type_launch_args: dict[str, object], pulse_settings: PulseSettings
) -> dict[str, object]:
    return {**browser_type_launch_args, "headless": pulse_settings.headless}


@pytest.fixture(scope="session")
def browser_context_args(
    browser_context_args: dict[str, object], pulse_settings: PulseSettings
) -> dict[str, object]:
    return {**browser_context_args, "base_url": pulse_settings.base_url}
```

- [ ] **Step 5: Register the fixtures conditionally in `src/pulse_tf/plugin.py`**

```python
"""pytest11 entry point for pulse-tf. Fixtures are registered here,
conditionally based on which optional extras are installed."""

from pulse_tf.config.settings import pulse_settings  # noqa: F401

try:
    import httpx  # noqa: F401
except ImportError:
    pass
else:
    from pulse_tf.api.factory import api_factory  # noqa: F401

try:
    import playwright  # noqa: F401
except ImportError:
    pass
else:
    from pulse_tf.web.fixtures import browser_context_args, browser_type_launch_args  # noqa: F401
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/web/test_fixtures.py -v`
Expected: 3 passed

- [ ] **Step 7: Run the full web test directory to confirm no regressions from Task 7**

Run: `uv run pytest tests/web -v`
Expected: all passed (Task 7's tests plus these)

- [ ] **Step 8: Commit**

```bash
git add src/pulse_tf/web/fixtures.py src/pulse_tf/plugin.py tests/web/conftest.py tests/web/test_fixtures.py
git commit -m "feat: inject PulseSettings into pytest-playwright browser/context args"
```

---

### Task 9: Web — screenshot-on-failure

**Files:**
- Modify: `src/pulse_tf/plugin.py`
- Modify: `tests/conftest.py` (enable the `pytester` plugin for this test)
- Test: `tests/web/test_screenshot_on_failure.py`

**Interfaces:**
- Consumes: `allure_utils.attach_screenshot` (Task 4).
- Produces: `pytest_runtest_makereport` hookimpl in `plugin.py` — on a failed test that used the `page` fixture, attaches a screenshot named `failure-<test-name>` to the Allure report.

- [ ] **Step 1: Create `tests/conftest.py`**

```python
pytest_plugins = ["pytester"]
```

- [ ] **Step 2: Write the failing test in `tests/web/test_screenshot_on_failure.py`**

```python
def test_screenshot_attached_on_failure(pytester, tmp_path):
    alluredir = tmp_path / "allure-results"
    pytester.makepyfile(
        """
        def test_that_fails(page):
            page.goto("about:blank")
            assert False
        """
    )
    result = pytester.runpytest("--browser", "chromium", f"--alluredir={alluredir}")
    result.assert_outcomes(failed=1)
    result_files = list(alluredir.glob("*-result.json"))
    assert result_files
    content = result_files[0].read_text()
    assert "failure-test_that_fails" in content
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `uv run pytest tests/web/test_screenshot_on_failure.py -v`
Expected: FAIL — no `*-result.json` contains a `failure-test_that_fails` attachment name (the hook doesn't exist yet).

- [ ] **Step 4: Replace `src/pulse_tf/plugin.py` with its full, final contents**

```python
"""pytest11 entry point for pulse-tf. Fixtures are registered here,
conditionally based on which optional extras are installed."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest

from pulse_tf.config.settings import pulse_settings  # noqa: F401

try:
    import httpx  # noqa: F401
except ImportError:
    pass
else:
    from pulse_tf.api.factory import api_factory  # noqa: F401

try:
    import playwright  # noqa: F401
except ImportError:
    pass
else:
    from pulse_tf.web.fixtures import browser_context_args, browser_type_launch_args  # noqa: F401


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, Any, None]:
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page is not None:
            # Best-effort: a failing test may have already closed/crashed the
            # page, and a broken screenshot must never mask the real failure.
            try:
                from pulse_tf.reporting import allure_utils

                allure_utils.attach_screenshot(page.screenshot(), name=f"failure-{item.name}")
            except Exception:
                pass
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `uv run pytest tests/web/test_screenshot_on_failure.py -v`
Expected: 1 passed

- [ ] **Step 6: Run the full test suite to confirm no regressions**

Run: `uv run pytest tests/ -v`
Expected: all passed

- [ ] **Step 7: Commit**

```bash
git add src/pulse_tf/plugin.py tests/conftest.py tests/web/test_screenshot_on_failure.py
git commit -m "feat: attach screenshot to Allure report on test failure"
```

---

### Task 10: CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: nothing new — runs the full test/lint/typecheck/build pipeline established in Tasks 1–9.

- [ ] **Step 1: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: uv sync --all-extras
      - name: Install Playwright browsers
        run: uv run playwright install --with-deps chromium
      - name: Lint
        run: uv run ruff check .
      - name: Type check
        run: uv run mypy src/pulse_tf
      - name: Test
        run: uv run pytest
      - name: Build package
        run: uv build
```

- [ ] **Step 2: Verify each CI command passes locally**

Run in sequence:
```bash
uv run ruff check .
uv run mypy src/pulse_tf
uv run pytest
uv build
```
Expected: each command exits 0. Fix any lint/type errors surfaced (they were not caught by earlier per-task test runs, which only ran `pytest`, not `ruff`/`mypy`).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions workflow (lint, typecheck, test, build)"
```

---

### Task 11: Examples and README

**Files:**
- Create: `examples/__init__.py`, `examples/conftest.py`
- Create: `examples/api/__init__.py`, `examples/api/clients/__init__.py`, `examples/api/clients/user_client.py`, `examples/api/test_users.py`
- Create: `examples/web/__init__.py`, `examples/web/conftest.py`, `examples/web/fixtures/index.html`, `examples/web/pages/__init__.py`, `examples/web/pages/login_page.py`, `examples/web/test_login.py`
- Create: `README.md`

**Interfaces:**
- Consumes: `BaseAPIClient` (Task 5), `APIClientFactory`/`api_factory` fixture (Task 6), `BasePage` (Task 7), `pulse_settings` fixture (Task 2).
- Produces: a runnable sample suite demonstrating both extension patterns end-to-end; no new library code.

- [ ] **Step 1: Create `examples/__init__.py`** (empty file)

- [ ] **Step 2: Create the API example — `examples/api/clients/user_client.py`**

```python
from pulse_tf.api.base_client import BaseAPIClient


class UserServiceClient(BaseAPIClient):
    def get_user(self, user_id: str) -> dict:
        return self.get(f"/users/{user_id}").json()
```

Also create `examples/api/__init__.py` and `examples/api/clients/__init__.py` (empty files).

- [ ] **Step 3: Create `examples/conftest.py`** (overrides `pulse_settings`, registers the client)

```python
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
```

- [ ] **Step 4: Write the API example test — `examples/api/test_users.py`**

```python
import httpx
import respx

from pulse_tf.api.factory import APIClientFactory


@respx.mock
def test_get_user(api_factory: APIClientFactory):
    respx.get("https://users.example/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Ada"})
    )
    client = api_factory.create("users")
    user = client.get_user("1")
    assert user == {"id": 1, "name": "Ada"}
```

- [ ] **Step 5: Run the API example**

Run: `uv run pytest examples/api -v`
Expected: 1 passed

- [ ] **Step 6: Create the web example — `examples/web/pages/login_page.py`**

```python
from pulse_tf.web.base_page import BasePage


class LoginPage(BasePage):
    USERNAME = "#username"
    PASSWORD = "#password"
    SUBMIT = "#submit"
    GREETING = "#greeting"

    def login(self, username: str, password: str) -> None:
        self.fill(self.USERNAME, username)
        self.fill(self.PASSWORD, password)
        self.click(self.SUBMIT)
```

Also create `examples/web/__init__.py` and `examples/web/pages/__init__.py` (empty files).

- [ ] **Step 7: Create `examples/web/fixtures/index.html`** (identical content to `tests/web/fixtures/index.html`)

```html
<!DOCTYPE html>
<html>
<body>
  <input id="username" />
  <input id="password" type="password" />
  <button id="submit">Login</button>
  <p id="greeting" style="display:none">Welcome!</p>
  <script>
    document.getElementById('submit').addEventListener('click', function () {
      document.getElementById('greeting').style.display = 'block';
    });
  </script>
</body>
</html>
```

- [ ] **Step 8: Create `examples/web/conftest.py`** (local static server + `pulse_settings` override for this subtree, overriding `examples/conftest.py`'s version)

```python
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
```

- [ ] **Step 9: Write the web example test — `examples/web/test_login.py`**

```python
from examples.web.pages.login_page import LoginPage


def test_login_shows_greeting(page, pulse_settings):
    login_page = LoginPage(page, pulse_settings)
    login_page.navigate("/index.html")
    login_page.login("bob", "secret")
    assert login_page.get_text(login_page.GREETING) == "Welcome!"
```

- [ ] **Step 10: Run the web example**

Run: `uv run pytest examples/web -v`
Expected: 1 passed

- [ ] **Step 11: Write `README.md`**

```markdown
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
```

- [ ] **Step 12: Run the entire suite one final time**

Run: `uv run pytest -v`
Expected: all passed (tests/ and examples/ together)

- [ ] **Step 13: Commit**

```bash
git add examples README.md
git commit -m "docs: add README and runnable example suite"
```
