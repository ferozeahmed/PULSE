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
