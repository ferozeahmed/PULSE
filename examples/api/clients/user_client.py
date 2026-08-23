from pulse_tf.api.base_client import BaseAPIClient


class UserServiceClient(BaseAPIClient):
    def get_user(self, user_id: str) -> dict:
        return self.get(f"/users/{user_id}").json()
