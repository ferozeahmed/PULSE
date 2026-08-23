from pulse_tf.web.base_page import BasePage


class LoginPage(BasePage):
    USERNAME = "#username"
    PASSWORD = "#password"
    SUBMIT = "#submit"
    GREETING = "#greeting"

    def login(self, username: str, password: str) -> None:
        self.fill(self.USERNAME, username)
        self.fill(self.PASSWORD, password)
        self.click(self.SUBMIT)
