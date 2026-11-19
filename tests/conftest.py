"""Shared fixtures for the GreenSpace-LST console suite.

The console (the Next.js app in the GIS repo) must be running; point the suite at it with
``--base-url`` (default in pyproject.toml: http://127.0.0.1:3000).

Data: the console's database is still experimental, so by default every ``/api`` read is answered
from the data files the app repo ships (``public/data``), which are byte-for-byte what the API
serves. Set ``QC_API=live`` to let requests reach the real API and database instead.
"""

import json
import os
from pathlib import Path

import pytest
from playwright.sync_api import BrowserContext, Page, Route

# The results table printed after each run (tests/summary.py); pytest finds hooks by name here.
from summary import pytest_runtest_makereport, pytest_terminal_summary  # noqa: F401

# The app repo's data files, next to this repo by default.
DATA_DIR = Path(os.environ.get("QC_DATA_DIR", Path(__file__).resolve().parents[2] / "! QC - GIS" / "GIS" / "public" / "data"))
LIVE = os.environ.get("QC_API", "mock") == "live"

# The only hosts the console reaches outside its own server: the map background tiles.
TILE_HOSTS = ("arcgisonline.com", "openstreetmap.org")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    # Reduced motion: tests never wait on transitions (the app turns animations off for it).
    return {**browser_context_args, "viewport": {"width": 1440, "height": 900}, "reduced_motion": "reduce"}


def _serve(route: Route, path: Path, content_type: str) -> None:
    route.fulfill(status=200, content_type=content_type, body=path.read_bytes())


def _mock_api(route: Route) -> None:
    """Answer /api reads from the app's data files; writes are refused so no test changes data."""
    request = route.request
    url = request.url.split("?")[0]
    if request.method != "GET":
        route.fulfill(status=503, json={"error": "writes are disabled in mock mode", "hint": "run with QC_API=live"})
    elif url.endswith("/api/safenet"):
        _serve(route, DATA_DIR / "safenet.json", "application/json")
    elif url.endswith("/api/osm"):
        _serve(route, DATA_DIR / "osm.json", "application/json")
    elif "/api/osm/" in url:
        # The API sends each layer gzipped without saying so; the .gsv.gz file is exactly that.
        layer = DATA_DIR / "osm" / (url.rsplit("/", 1)[1] + ".gsv.gz")
        if layer.exists():
            _serve(route, layer, "application/octet-stream")
        else:
            route.fulfill(status=404, json={"error": "unknown layer"})
    elif url.endswith("/api/facilities"):
        route.fulfill(json={"type": "FeatureCollection", "features": []})
    elif url.endswith("/api/uploads"):
        route.fulfill(json={"uploads": []})
    else:
        route.continue_()


@pytest.fixture
def api(context: BrowserContext) -> str:
    """Route the console's API to the shipped data files (default) or leave it live."""
    if not LIVE:
        if not (DATA_DIR / "safenet.json").exists():
            pytest.skip(f"no data files at {DATA_DIR}; set QC_DATA_DIR or run with QC_API=live")
        context.route("**/api/**", _mock_api)
    return "live" if LIVE else "mock"


@pytest.fixture
def page_errors(page: Page) -> list[str]:
    """Uncaught page errors; every test that uses ``console`` fails if one happens."""
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    return errors


@pytest.fixture
def offline(context: BrowserContext):
    """Simulate a laptop with no internet: tile servers unreachable, navigator.onLine false.

    context.set_offline() would also cut the console's own server (localhost), so the outside
    world is blocked by host instead. Call ``reconnect()`` on the result to bring it back.
    """

    def outside(url: str) -> bool:
        return any(host in url for host in TILE_HOSTS)

    def block(route: Route) -> None:
        route.abort("internetdisconnected")

    context.route(outside, block)
    context.add_init_script("Object.defineProperty(Navigator.prototype, 'onLine', { configurable: true, get: () => window.__online ?? false });")

    class Switch:
        def reconnect(self, page: Page) -> None:
            context.unroute(outside, block)
            page.evaluate("window.__online = true; window.dispatchEvent(new Event('online'))")

    return Switch()


@pytest.fixture
def console(page: Page, api: str, page_errors: list[str]):
    """The console, opened and painted, as a page object. Fails the test on any page error."""
    from pages.console import ConsolePage

    yield ConsolePage(page)
    assert page_errors == [], f"page errors: {json.dumps(page_errors, indent=1)}"
