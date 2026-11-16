"""The Compare view (``/?tab=compare``): two maps, each with its own layer buttons and opacity bar."""

from playwright.sync_api import Page, expect

from pages.console import CITY_BOX, RASTER_OPACITY, SET_RANGE, wait_for_opacities


class ComparePage:
    def __init__(self, page: Page):
        self.page = page

    def open(self) -> "ComparePage":
        self.page.goto("/?tab=compare")
        for side in ("A", "B"):
            expect(self.page.locator(f"#cmp{side} canvas.leaflet-tile").first).to_be_attached(timeout=60_000)
        return self

    def map(self, side: str):
        return self.page.locator(f"#cmp{side.upper()}")

    def opacity_bar(self, side: str):
        return self.page.locator(f"#cmp-op-{side.lower()}")

    def set_opacity(self, side: str, percent: int) -> None:
        self.opacity_bar(side).evaluate(SET_RANGE, percent)

    def raster_opacities(self, side: str) -> list[float]:
        return self.map(side).evaluate(RASTER_OPACITY)

    def expect_raster_opacities(self, side: str, expected: list[float]) -> None:
        wait_for_opacities(self.page, f"#cmp{side.upper()}", expected)

    def city_box(self, side: str) -> dict:
        return self.map(side).evaluate(CITY_BOX)
