"""The side panels fold to a strip without moving the map, and remember it."""

from playwright.sync_api import expect


def test_folding_both_panels_leaves_the_map_still(console):
    console.open()
    before = console.city_box()
    console.toggle_left()
    console.toggle_right()
    expect(console.left_panel).to_have_attribute("data-collapsed", "true")
    expect(console.right_panel).to_have_attribute("data-collapsed", "true")
    after = console.city_box()
    assert abs(after["left"] - before["left"]) < 2 and abs(after["top"] - before["top"]) < 2


def test_panels_never_resize_the_map(console):
    console.open()
    width = console.map.bounding_box()["width"]
    console.toggle_left()
    console.toggle_right()
    assert console.map.bounding_box()["width"] == width


def test_folded_panels_survive_a_reload(console):
    console.open()
    console.toggle_left()
    console.page.reload()
    expect(console.left_panel).to_have_attribute("data-collapsed", "true")
    expect(console.right_panel).to_have_attribute("data-collapsed", "false")


def test_section_icon_opens_the_panel_at_that_section(console):
    console.open()
    console.toggle_left()
    console.page.get_by_role("button", name="Show basemap").click()
    expect(console.left_panel).to_have_attribute("data-collapsed", "false")
    expect(console.left_panel.get_by_role("heading", name="Basemap")).to_be_in_viewport()
