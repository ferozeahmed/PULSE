from pulse_tf.web.base_page import BasePage


def test_navigate_and_interact(page, static_server_url):
    pg = BasePage(page)
    pg.navigate(f"{static_server_url}/index.html")
    pg.fill("#username", "bob")
    pg.fill("#password", "secret")
    assert pg.is_visible("#greeting") is False
    pg.click("#submit")
    pg.wait_for("#greeting")
    assert pg.is_visible("#greeting") is True


def test_get_text_reads_element(page, static_server_url):
    pg = BasePage(page)
    pg.navigate(f"{static_server_url}/index.html")
    pg.click("#submit")
    assert pg.get_text("#greeting") == "Welcome!"
