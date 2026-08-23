from examples.web.pages.login_page import LoginPage


def test_login_shows_greeting(page, pulse_settings):
    login_page = LoginPage(page, pulse_settings)
    login_page.navigate("/index.html")
    login_page.login("bob", "secret")
    assert login_page.get_text(login_page.GREETING) == "Welcome!"
