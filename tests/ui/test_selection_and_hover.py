"""Picking a barangay, the island, and the hover details."""

import re

from playwright.sync_api import expect


def test_picking_a_barangay_shows_it_in_the_island_and_the_address(console):
    console.open()
    console.select_barangay("Pasong Tamo")
    expect(console.island).to_contain_text("Pasong Tamo")
    expect(console.page).to_have_url(re.compile(r"select=Pasong(\+|%20)Tamo"))


def test_a_shared_link_opens_on_the_barangay(console):
    console.open("select=Pasong+Tamo")
    expect(console.island).to_contain_text("Pasong Tamo")


def test_hover_details_never_cover_the_island(console):
    console.open("select=Pasong+Tamo")
    expect(console.island).to_be_visible()
    console.page.wait_for_timeout(3500)  # the island's auto-expand after a selection settles
    island = console.island.bounding_box()
    # Sweep a band of cursor positions right under and beside the island.
    for x in range(int(island["x"]) - 120, int(island["x"] + island["width"]) + 120, 40):
        for y in (island["y"] + island["height"] + 4, island["y"] + island["height"] + 40, island["y"] + island["height"] + 120):
            console.page.mouse.move(x, y)
            tip = console.hover_details.bounding_box() if console.hover_details.is_visible() else None
            if tip is None:
                continue
            now = console.island.bounding_box()
            overlap = tip["x"] < now["x"] + now["width"] and tip["x"] + tip["width"] > now["x"] and tip["y"] < now["y"] + now["height"] and tip["y"] + tip["height"] > now["y"]
            assert not overlap, f"hover details cover the island with the cursor at {x},{y}"


def test_hover_details_follow_the_cursor_and_hide_off_the_map(console):
    console.open()
    box = console.map.bounding_box()
    console.page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    expect(console.hover_details).to_be_visible()
    console.page.mouse.move(5, box["y"] + box["height"] + 20)  # onto the bottom bar
    expect(console.hover_details).to_be_hidden()
