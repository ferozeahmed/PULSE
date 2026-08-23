import os
import sys
from pathlib import Path

pytest_plugins = ["pytester"]

# The `pytester` fixture sandboxes HOME/USERPROFILE to a throwaway temp
# directory for the duration of each test that requests it (see
# _pytest.pytester.Pytester._initpath), to isolate inner pytest runs from the
# outer user's config files. Playwright's driver resolves its browser cache
# directory (where `playwright install` puts browsers) relative to HOME
# unless PLAYWRIGHT_BROWSERS_PATH is set explicitly, so any pytester-driven
# test that spins up a `page` fixture would otherwise fail with "Executable
# doesn't exist" because the sandboxed HOME has no browsers installed under
# it. Pin PLAYWRIGHT_BROWSERS_PATH to the real, already-installed cache (if
# one is found) so inner pytest runs can still locate the browsers, unless
# the environment already sets it explicitly (e.g. CI).
if "PLAYWRIGHT_BROWSERS_PATH" not in os.environ:
    if sys.platform == "darwin":
        _default_browsers_path = Path.home() / "Library" / "Caches" / "ms-playwright"
    elif sys.platform == "win32":
        _default_browsers_path = Path.home() / "AppData" / "Local" / "ms-playwright"
    else:
        _cache_home = os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))
        _default_browsers_path = Path(_cache_home) / "ms-playwright"
    if _default_browsers_path.is_dir():
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(_default_browsers_path)
