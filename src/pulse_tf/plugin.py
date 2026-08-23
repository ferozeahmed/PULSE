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
    # Registered from pytest_configure (rather than imported at module level,
    # like the httpx/api_factory block above) so that pulse-tf's
    # browser_type_launch_args/browser_context_args overrides are parsed
    # *after* pytest-playwright's own same-named fixtures. pytest resolves
    # same-name, same-visibility fixture collisions across plugins by
    # registration order (last registered wins), and pytest11 entry-point
    # scan order across distributions is not something pulse-tf controls, so
    # a plain module-level import here could non-deterministically be shadowed
    # by pytest-playwright's originals instead of overriding them.
    def pytest_configure(config: pytest.Config) -> None:
        from pulse_tf.web import fixtures as web_fixtures

        config.pluginmanager.register(web_fixtures, name="pulse_tf_web_fixtures")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, Any, None]:
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        # funcargs lives on pytest.Function (not the base pytest.Item type
        # mypy sees here), so look it up defensively.
        page = getattr(item, "funcargs", {}).get("page")
        if page is not None:
            # Best-effort: a failing test may have already closed/crashed the
            # page, and a broken screenshot must never mask the real failure.
            try:
                from pulse_tf.reporting import allure_utils

                allure_utils.attach_screenshot(page.screenshot(), name=f"failure-{item.name}")
            except Exception:
                pass
