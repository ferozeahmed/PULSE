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
