"""The console page (``/``): map, side panels, layers, selection and the bottom bar.

Locators prefer the roles and labels the app already exposes; a few stable ids and classes stand
in where there is no role (the map, the island, the hover details, the offline pill).
"""

from playwright.sync_api import Locator, Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# A range input is set the way a drag sets it: native setter, then the input event React listens to.
SET_RANGE = """(el, value) => {
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, String(value));
  el.dispatchEvent(new Event('input', { bubbles: true }));
}"""

# Bounding box of the barangay outlines inside a map: where the city sits on screen.
CITY_BOX = """(map) => {
  const boxes = [...map.querySelectorAll('path.leaflet-interactive')].map((p) => p.getBoundingClientRect()).filter((b) => b.width > 0);
  return { left: Math.min(...boxes.map((b) => b.left)), top: Math.min(...boxes.map((b) => b.top)),
           right: Math.max(...boxes.map((b) => b.right)), bottom: Math.max(...boxes.map((b) => b.bottom)) };
}"""

# Opacity of every raster layer (the containers that hold painted canvas tiles).
RASTER_OPACITY = """(map) => [...map.querySelectorAll('.leaflet-layer')]
  .filter((layer) => layer.querySelector('canvas.leaflet-tile'))
  .map((layer) => Number(getComputedStyle(layer).opacity))"""


def wait_for_opacities(page: Page, root: str, expected: list[float]) -> None:
    check = f"([root, want]) => JSON.stringify(({RASTER_OPACITY})(document.querySelector(root))) === JSON.stringify(want)"
    try:
        page.wait_for_function(check, arg=[root, expected], timeout=5_000)
    except PlaywrightTimeoutError:
        assert page.locator(root).evaluate(RASTER_OPACITY) == expected


class ConsolePage:
    def __init__(self, page: Page):
        self.page = page
        self.map = page.locator("#map")
        self.zoom_label = page.locator("#mapctl .zl")
        self.island = page.locator(".island")
        self.hover_details = page.locator(".hovertip")
        self.offline_pill = page.locator(".offlinepill")
        self.map_note = page.locator(".mapnote")
        self.overlay = page.locator("#op")
        self.left_panel = page.locator(".rail-left")
        self.right_panel = page.locator(".rail-right")

    # ---- navigation
    def open(self, query: str = "") -> "ConsolePage":
        self.page.goto("/" + (f"?{query}" if query else ""))
        # Only the console tab mounts the map on load; other tabs mount on first visit.
        if "tab=" not in query or "tab=console" in query:
            self.wait_painted()
        return self

    def wait_painted(self, root: str = "#map") -> None:
        expect(self.page.locator(f"{root} canvas.leaflet-tile").first).to_be_attached(timeout=60_000)

    def tab(self, name: str) -> Locator:
        return self.page.get_by_role("tab", name=name)

    def go_to_view(self, name: str) -> None:
        self.tab(name).click()
        expect(self.tab(name)).to_have_attribute("aria-selected", "true")

    # ---- map
    def zoom_level(self) -> float:
        return float(self.zoom_label.inner_text().lstrip("z"))

    def zoom_out(self, times: int = 1) -> None:
        for _ in range(times):
            self.page.get_by_role("button", name="Zoom out").click()
        self.wait_still()

    def zoom_in(self, times: int = 1) -> None:
        for _ in range(times):
            self.page.get_by_role("button", name="Zoom in").click()
        self.wait_still()

    def wait_still(self, root: str = "#map") -> None:
        """Wait until the city stops moving on screen (zoom and pan animations have landed)."""
        last = None
        for _ in range(40):
            now = self.city_box(root)
            if now == last:
                return
            last = now
            self.page.wait_for_timeout(250)

    def drag_map(self, dx: float, dy: float, start: tuple[float, float] | None = None) -> None:
        box = self.map.bounding_box()
        x, y = start or (box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        self.page.mouse.move(x, y)
        self.page.mouse.down()
        self.page.mouse.move(x + dx, y + dy, steps=12)
        self.page.mouse.up()
        self.wait_still()

    def city_box(self, root: str = "#map") -> dict:
        return self.page.locator(root).evaluate(CITY_BOX)

    def raster_opacities(self, root: str = "#map") -> list[float]:
        return self.page.locator(root).evaluate(RASTER_OPACITY)

    def expect_raster_opacities(self, expected: list[float], root: str = "#map") -> None:
        """Wait (up to 5 s) for the raster layers to reach these opacities: React applies a bar change on its next render."""
        wait_for_opacities(self.page, root, expected)

    # ---- left panel
    def layer(self, name: str) -> Locator:
        return self.left_panel.locator(".layer", has_text=name)

    def switch(self, label: str) -> Locator:
        return self.page.get_by_role("switch", name=label)

    def set_overlay(self, percent: int) -> None:
        self.overlay.evaluate(SET_RANGE, percent)

    # ---- side panels
    def toggle_left(self) -> None:
        self.left_panel.locator(".railhead > .railtoggle").first.click()

    def toggle_right(self) -> None:
        self.right_panel.locator(".railhead > .railtoggle").first.click()

    # ---- selection
    def select_barangay(self, name: str) -> None:
        self.page.locator(".picker-trigger").first.click()
        self.page.get_by_role("searchbox", name="Filter Barangay").fill(name)
        self.page.get_by_role("listbox", name="Barangay").get_by_role("option", name=name, exact=True).click()
