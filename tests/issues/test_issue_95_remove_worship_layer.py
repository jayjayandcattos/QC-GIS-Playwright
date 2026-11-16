"""#95: remove the places-of-worship reference layer.

Done when: no "Places of worship" toggle, no request for its file, no console errors.
"""

from playwright.sync_api import expect


def test_reference_toggles_have_no_places_of_worship(console):
    console.open()
    expect(console.switch("Places of worship")).to_have_count(0)
    for label in ("Major roads", "Rivers and water", "Land use", "City boundary"):
        expect(console.switch(label)).to_have_count(1)


def test_no_request_for_the_worship_file_with_every_layer_on(console):
    asked: list[str] = []
    console.page.on("request", lambda request: asked.append(request.url) if "worship" in request.url.lower() else None)
    console.open()
    for toggle in console.left_panel.get_by_role("switch").all():
        if toggle.get_attribute("aria-checked") == "false":
            toggle.click()
    for view in ("Compare", "Relationship", "Barangays", "Method", "Console"):
        console.go_to_view(view)
    console.page.wait_for_timeout(1500)
    assert asked == []
