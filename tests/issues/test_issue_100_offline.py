"""#100: the console works offline (after one online visit, served from the laptop).

Done when: with no network the console and every view load, the map shows a background, and
whatever cannot work offline says so instead of failing silently or leaving a blank area.
"""

import pytest
from playwright.sync_api import expect

from pages.compare import ComparePage

OFFLINE_CANVASES = ".leaflet-tile-pane canvas.vector-canvas"


def test_offline_shows_the_pill_the_note_and_the_offline_background(console, offline):
    console.open()
    expect(console.offline_pill).to_have_text("Offline")
    expect(console.map_note).to_contain_text("No internet")
    expect(console.map.locator(OFFLINE_CANVASES).first).to_be_attached()
    expect(console.map.locator(".leaflet-tile-pane img.leaflet-tile")).to_have_count(0)


def test_satellite_offline_says_it_needs_internet(console, offline):
    console.open()
    console.page.locator('[data-basemap="satellite"]').click()
    expect(console.map_note).to_contain_text("Satellite imagery needs internet")


@pytest.mark.parametrize("view", ["Compare", "Relationship", "Barangays", "Method"])
def test_every_view_loads_offline(console, offline, view):
    console.open()
    console.go_to_view(view)
    section = console.page.locator(f"#view-{view.lower()}")
    expect(section).to_be_visible()
    expect(section).not_to_contain_text("Could not load")


def test_compare_maps_use_the_offline_background(page, api, offline):
    compare = ComparePage(page).open()
    for side in ("a", "b"):
        expect(compare.map(side).locator(OFFLINE_CANVASES).first).to_be_attached()


def test_tiles_come_back_when_the_connection_does(console, offline):
    console.open()
    expect(console.offline_pill).to_be_visible()
    offline.reconnect(console.page)
    expect(console.offline_pill).to_have_count(0)
    expect(console.map_note).to_have_count(0)
    expect(console.map.locator(".leaflet-tile-pane img.leaflet-tile").first).to_be_attached()
