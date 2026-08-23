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
