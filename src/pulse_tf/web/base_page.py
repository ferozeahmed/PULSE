from __future__ import annotations

from typing import Literal

from playwright.sync_api import Page

from pulse_tf.config.settings import PulseSettings
from pulse_tf.logging.logger import get_logger
from pulse_tf.reporting import allure_utils

_logger = get_logger("pulse_tf.web")


class BasePage:
    def __init__(self, page: Page, settings: PulseSettings | None = None) -> None:
        self.page = page
        self.settings = settings

    def navigate(self, url: str) -> None:
        with allure_utils.step(f"Navigate to {url}"):
            _logger.info("navigate: %s", url)
            self.page.goto(url)

    def click(self, locator: str) -> None:
        with allure_utils.step(f"Click {locator}"):
            _logger.info("click: %s", locator)
            self.page.locator(locator).click()

    def fill(self, locator: str, text: str) -> None:
        with allure_utils.step(f"Fill {locator}"):
            _logger.info("fill: %s", locator)
            self.page.locator(locator).fill(text)

    def get_text(self, locator: str) -> str:
        with allure_utils.step(f"Get text {locator}"):
            return self.page.locator(locator).inner_text()

    def is_visible(self, locator: str) -> bool:
        return self.page.locator(locator).is_visible()

    def wait_for(
        self,
        locator: str,
        *,
        state: Literal["attached", "detached", "hidden", "visible"] = "visible",
    ) -> None:
        with allure_utils.step(f"Wait for {locator} ({state})"):
            self.page.locator(locator).wait_for(state=state)

    def screenshot(self, name: str = "screenshot") -> bytes:
        data = self.page.screenshot()
        allure_utils.attach_screenshot(data, name=name)
        return data
