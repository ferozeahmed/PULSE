"""pytest11 entry point for pulse-tf. Fixtures are registered here,
conditionally based on which optional extras are installed."""

from pulse_tf.config.settings import pulse_settings  # noqa: F401

try:
    import httpx  # noqa: F401
except ImportError:
    pass
else:
    from pulse_tf.api.factory import api_factory  # noqa: F401
