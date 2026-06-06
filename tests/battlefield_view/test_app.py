from olden.battlefield_view.app import render_battlefield_svg
from olden.battlefield_view.model import build_battlefield_view
from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.occupancy import Occupancy


def test_svg_renderer_outputs_one_polygon_per_renderable_hex_and_unit_label():
    occupancy = Occupancy()
    occupancy.place("unit-1", HexCoord(4, 5))
    view = build_battlefield_view(Battlefield.default(), occupancy)

    svg = render_battlefield_svg(view)

    assert svg.startswith("<svg ")
    assert svg.count("<polygon ") == 137
    assert "unit-1" in svg
