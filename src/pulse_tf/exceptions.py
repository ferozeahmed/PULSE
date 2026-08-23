from __future__ import annotations


class PulseConfigError(Exception):
    """Raised when PulseSettings fails validation, or an API client factory
    lookup can't be resolved."""


class PulseAPIError(Exception):
    def __init__(self, message: str, *, status_code: int, response_body: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
