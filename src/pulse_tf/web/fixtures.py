from __future__ import annotations

import pytest

from pulse_tf.config.settings import PulseSettings


@pytest.fixture(scope="session")
def browser_type_launch_args(
    browser_type_launch_args: dict[str, object], pulse_settings: PulseSettings
) -> dict[str, object]:
    # Only override pytest-playwright's own CLI-derived value (e.g. `--headed`)
    # when the user actually configured `headless` on pulse_settings (via env
    # var, .env file, or an explicit pulse_settings override) — not merely
    # because it matches PulseSettings' default. `model_fields_set` reflects
    # what was explicitly provided during construction, not the resolved
    # value, so a field left untouched never appears in it even if its
    # default happens to equal the current value.
    if "headless" not in pulse_settings.model_fields_set:
        return browser_type_launch_args
    return {**browser_type_launch_args, "headless": pulse_settings.headless}


@pytest.fixture(scope="session")
def browser_context_args(
    browser_context_args: dict[str, object], pulse_settings: PulseSettings
) -> dict[str, object]:
    # Same rationale as browser_type_launch_args above: don't clobber
    # pytest-playwright's own `--base-url` unless pulse_settings.base_url was
    # explicitly set.
    if "base_url" not in pulse_settings.model_fields_set:
        return browser_context_args
    return {**browser_context_args, "base_url": pulse_settings.base_url}
