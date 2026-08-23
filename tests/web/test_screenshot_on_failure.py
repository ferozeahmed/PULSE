def test_screenshot_attached_on_failure(pytester, tmp_path):
    alluredir = tmp_path / "allure-results"
    pytester.makepyfile(
        """
        def test_that_fails(page):
            page.goto("about:blank")
            assert False
        """
    )
    # runpytest_subprocess (not runpytest): pytest-playwright wraps every
    # test's call phase in a non-reentrant global soft-assertion scope
    # (playwright._impl._assertions._soft_scope). Running the inner suite
    # in-process would re-enter that same scope from within this outer test
    # and raise "nested soft assertion scopes are not supported". A real
    # subprocess gets its own fresh module state and avoids the collision.
    result = pytester.runpytest_subprocess("--browser", "chromium", f"--alluredir={alluredir}")
    result.assert_outcomes(failed=1)
    result_files = list(alluredir.glob("*-result.json"))
    assert result_files
    content = result_files[0].read_text()
    assert "failure-test_that_fails" in content
