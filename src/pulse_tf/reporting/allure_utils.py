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
