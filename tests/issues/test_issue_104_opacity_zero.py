"""#104: allow 0% layer opacity.

Done when: any opacity bar goes to 0%, the layer disappears completely, the bar reads "0%", the
layer stays switched on, and dragging back up restores it without toggling anything.
"""

from playwright.sync_api import expect

from pages.compare import ComparePage


def test_console_overlay_goes_to_zero_and_back(console):
    console.open()
    expect(console.overlay).to_have_attribute("min", "0")
    console.set_overlay(0)
    expect(console.page.locator("#op-out")).to_have_text("0")
    console.expect_raster_opacities([0])
    expect(console.layer("Vegetation index")).to_have_attribute("aria-pressed", "true")
    console.set_overlay(78)
    console.expect_raster_opacities([0.78])


def test_stacked_layers_both_disappear_at_zero(console):
    console.open()
    console.switch("Stack NDVI and LST").click()
    expect(console.map.locator(".leaflet-layer:has(canvas.leaflet-tile)")).to_have_count(2)
    console.set_overlay(0)
    console.expect_raster_opacities([0, 0])


def test_hover_and_selection_still_work_at_zero(console):
    console.open()
    console.set_overlay(0)
    box = console.map.bounding_box()
    console.page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    expect(console.hover_details).to_be_visible()


def test_compare_bars_go_to_zero_and_back(page, api):
    compare = ComparePage(page).open()
    for side in ("a", "b"):
        expect(compare.opacity_bar(side)).to_have_attribute("min", "0")
        compare.set_opacity(side, 0)
        compare.expect_raster_opacities(side, [0])
        compare.set_opacity(side, 78)
        compare.expect_raster_opacities(side, [0.78])
