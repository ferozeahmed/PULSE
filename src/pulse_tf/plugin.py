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
    import pytest

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
