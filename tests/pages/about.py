"""The presentation page (``/about``) shown before the console."""

import re

from playwright.sync_api import Page, expect


class AboutPage:
    def __init__(self, page: Page):
        self.page = page
        self.title = page.get_by_role("heading", level=1)
        self.hero_image = page.locator(".about-shot img:visible")

    def open(self) -> "AboutPage":
        self.page.goto("/about")
        expect(self.title).to_be_visible()
        return self

    def view_link(self, view: str):
        # A card's name is its whole text, and "barangays" appears in other cards too: match the title.
        return self.page.locator(".about-views").get_by_role("link", name=re.compile(f"^{view}"))
