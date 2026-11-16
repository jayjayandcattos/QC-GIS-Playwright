"""The map stays on Quezon City: no zooming out past the whole city, no dragging it away."""

from pages.compare import ComparePage

# The city's box has a small margin around the outlines; allow it plus rounding.
SLACK = 40


def test_cannot_zoom_out_past_the_whole_city(console):
    console.open()
    console.zoom_out(6)
    floor = console.zoom_level()
    console.zoom_out(3)
    assert console.zoom_level() == floor
    city, view = console.city_box(), console.map.bounding_box()
    # At the floor the whole city is on screen (vertically it fills the view).
    assert city["top"] >= view["y"] - SLACK and city["bottom"] <= view["y"] + view["height"] + SLACK


def test_cannot_drag_the_city_away_when_zoomed_out(console):
    console.open()
    console.zoom_out(6)
    before = console.city_box()
    console.drag_map(400, 300)
    after = console.city_box()
    assert abs(after["left"] - before["left"]) < 2 and abs(after["top"] - before["top"]) < 2


def test_panning_stops_at_the_city_edge_when_zoomed_in(console):
    console.open()
    console.zoom_in(2)
    for _ in range(4):
        console.drag_map(600, 0)  # pull the west edge into view, hard
    left_panel_edge = console.left_panel.bounding_box()
    edge = left_panel_edge["x"] + left_panel_edge["width"] if left_panel_edge else console.map.bounding_box()["x"]
    # The city's west edge may come out to the panel's inner edge, but no further.
    assert console.city_box()["left"] <= edge + SLACK


def test_compare_maps_are_locked_too(page, api):
    compare = ComparePage(page).open()
    for side in ("a", "b"):
        box = compare.map(side).bounding_box()
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        for _ in range(8):
            page.mouse.wheel(0, 600)
            page.wait_for_timeout(150)
        page.wait_for_timeout(800)
        city = compare.city_box(side)
        # Zoomed out as far as it goes, the city still fills the map's height: no further out.
        assert city["bottom"] - city["top"] >= box["height"] * 0.8, (side, city, box)
