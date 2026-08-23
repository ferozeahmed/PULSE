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
