from __future__ import annotations

from typing import Any

import httpx

from pulse_tf.exceptions import PulseAPIError
from pulse_tf.logging.logger import get_logger, redact
from pulse_tf.reporting import allure_utils

_logger = get_logger("pulse_tf.api")


class BaseAPIClient:
    def __init__(self, base_url: str, *, client: httpx.Client | None = None) -> None:
        self.base_url = base_url
        self._client = client or httpx.Client(base_url=base_url)

    def get(self, path: str, *, raise_for_status: bool = True, **kwargs: Any) -> httpx.Response:
        return self._request("GET", path, raise_for_status=raise_for_status, **kwargs)

    def post(self, path: str, *, raise_for_status: bool = True, **kwargs: Any) -> httpx.Response:
        return self._request("POST", path, raise_for_status=raise_for_status, **kwargs)

    def put(self, path: str, *, raise_for_status: bool = True, **kwargs: Any) -> httpx.Response:
        return self._request("PUT", path, raise_for_status=raise_for_status, **kwargs)

    def patch(self, path: str, *, raise_for_status: bool = True, **kwargs: Any) -> httpx.Response:
        return self._request("PATCH", path, raise_for_status=raise_for_status, **kwargs)

    def delete(self, path: str, *, raise_for_status: bool = True, **kwargs: Any) -> httpx.Response:
        return self._request("DELETE", path, raise_for_status=raise_for_status, **kwargs)

    def _request(
        self, method: str, path: str, *, raise_for_status: bool, **kwargs: Any
    ) -> httpx.Response:
        step_name = f"{method} {self.base_url}{path}"
        with allure_utils.step(step_name):
            _logger.info(
                "%s request headers=%s", step_name, redact(dict(kwargs.get("headers") or {}))
            )
            response = self._client.request(method, path, **kwargs)
            _logger.info("%s -> %s", step_name, response.status_code)
            if raise_for_status and response.is_error:
                raise PulseAPIError(
                    f"{step_name} returned {response.status_code}",
                    status_code=response.status_code,
                    response_body=response.text,
                )
            return response
