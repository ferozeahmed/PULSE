import httpx
import respx

from pulse_tf.api.factory import APIClientFactory


@respx.mock
def test_get_user(api_factory: APIClientFactory):
    respx.get("https://users.example/users/1").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "Ada"})
    )
    client = api_factory.create("users")
    user = client.get_user("1")
    assert user == {"id": 1, "name": "Ada"}
