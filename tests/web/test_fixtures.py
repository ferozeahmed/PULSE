from pulse_tf.web.base_page import BasePage


def test_browser_context_args_includes_base_url(browser_context_args, pulse_settings):
    assert browser_context_args["base_url"] == pulse_settings.base_url


def test_browser_type_launch_args_includes_headless(browser_type_launch_args, pulse_settings):
    assert browser_type_launch_args["headless"] == pulse_settings.headless


def test_relative_navigate_resolves_against_base_url(page, pulse_settings):
    pg = BasePage(page, pulse_settings)
    pg.navigate("/index.html")
    assert pg.is_visible("#username") is True
