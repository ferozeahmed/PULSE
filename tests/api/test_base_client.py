import json
import logging

import httpx
import pytest
import respx

from pulse_tf.api.base_client import BaseAPIClient
from pulse_tf.exceptions import PulseAPIError
from pulse_tf.reporting import allure_utils


@pytest.fixture
def client():
    return BaseAPIClient("https://api.test")


@respx.mock
def test_get_returns_response(client):
    respx.get("https://api.test/users/1").mock(return_value=httpx.Response(200, json={"id": 1}))
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json() == {"id": 1}


@respx.mock
def test_non_2xx_raises_pulse_api_error_by_default(client):
    respx.get("https://api.test/users/99").mock(return_value=httpx.Response(404, text="not found"))
    with pytest.raises(PulseAPIError) as exc_info:
        client.get("/users/99")
    assert exc_info.value.status_code == 404
    assert exc_info.value.response_body == "not found"


@respx.mock
def test_raise_for_status_false_returns_error_response(client):
    respx.get("https://api.test/users/99").mock(return_value=httpx.Response(404, text="not found"))
    response = client.get("/users/99", raise_for_status=False)
    assert response.status_code == 404


@respx.mock
def test_post_sends_json_body(client):
    route = respx.post("https://api.test/users").mock(
        return_value=httpx.Response(201, json={"id": 2})
    )
    response = client.post("/users", json={"name": "bob"})
    assert response.status_code == 201
    assert route.called
    assert json.loads(route.calls.last.request.content) == {"name": "bob"}


def test_authorization_header_is_redacted_in_logs(client, caplog):
    with respx.mock:
        respx.get("https://api.test/secret").mock(return_value=httpx.Response(200))
        with caplog.at_level(logging.INFO, logger="pulse_tf.api"):
            client.get("/secret", headers={"Authorization": "Bearer topsecret"})
    assert "topsecret" not in caplog.text
    assert "REDACTED" in caplog.text


@respx.mock
def test_password_in_json_body_is_redacted_in_logs_and_attachments(client, caplog, monkeypatch):
    attachments: list[tuple[str, str]] = []
    monkeypatch.setattr(
        allure_utils,
        "attach_text",
        lambda data, name="log": attachments.append((data, name)),
    )
    respx.post("https://api.test/login").mock(return_value=httpx.Response(200, json={"ok": True}))

    with caplog.at_level(logging.INFO, logger="pulse_tf.api"):
        client.post("/login", json={"username": "bob", "password": "hunter2"})

    assert "hunter2" not in caplog.text
    assert "REDACTED" in caplog.text

    request_body_attachments = [data for data, name in attachments if "request body" in name]
    assert request_body_attachments, "expected a request-body attachment"
    assert "hunter2" not in request_body_attachments[0]
    assert "REDACTED" in request_body_attachments[0]

    response_body_attachments = [data for data, name in attachments if "response body" in name]
    assert response_body_attachments, "expected a response-body attachment"
    assert "ok" in response_body_attachments[0]
