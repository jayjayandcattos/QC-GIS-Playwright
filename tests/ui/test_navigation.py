"""Every view opens, and the pages link to each other."""

import re

import pytest
from playwright.sync_api import expect

from pages.about import AboutPage

VIEWS = ["Console", "Compare", "Relationship", "Barangays", "Method"]


@pytest.mark.parametrize("view", VIEWS)
def test_each_view_opens_from_the_bottom_bar(console, view):
    console.open()
    console.go_to_view(view)
    expect(console.page.locator(f"#view-{view.lower()}")).to_be_visible()


def test_view_is_kept_in_the_address(console):
    console.open("tab=barangays")
    expect(console.tab("Barangays")).to_have_attribute("aria-selected", "true")


def test_bottom_bar_reaches_about_and_upload(console):
    console.open()
    console.page.get_by_role("link", name="About").click()
    expect(console.page).to_have_url(re.compile(r"/about$"))
    console.page.go_back()
    console.page.get_by_role("link", name="Add or edit places").click()
    expect(console.page.get_by_role("heading", name="Add or edit places")).to_be_visible()


@pytest.mark.parametrize("view", ["Compare", "Relationship", "Barangays", "Method"])
def test_about_page_links_open_each_view(page, api, view):
    about = AboutPage(page).open()
    about.view_link(view).click()
    expect(page.get_by_role("tab", name=view)).to_have_attribute("aria-selected", "true")


def test_about_page_works_with_no_internet(page, api, offline):
    about = AboutPage(page).open()
    expect(about.hero_image).to_have_count(1)
    assert about.hero_image.evaluate("img => img.complete && img.naturalWidth > 0")
