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
