from olden.battlefield_view.app import _build_page, render_battlefield_svg
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
    assert 'width="' in svg
    assert 'fill="' in svg
    assert "unit-1" in svg


def test_nicegui_page_embeds_trusted_generated_svg_without_sanitizing():
    ui = FakeUi()
    view = build_battlefield_view(Battlefield.default(), Occupancy())

    _build_page(ui, view)

    assert ui.html_sanitize is False


class FakeUi:
    def __init__(self) -> None:
        self.html_sanitize: bool | None = None

    def page_title(self, title: str) -> None:
        pass

    def add_css(self, css: str) -> None:
        pass

    def column(self) -> "FakeElement":
        return FakeElement()

    def html(self, content: str, *, sanitize: bool = True) -> "FakeElement":
        self.html_sanitize = sanitize
        return FakeElement()


class FakeElement:
    def classes(self, classes: str) -> "FakeElement":
        return self

    def __enter__(self) -> "FakeElement":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        pass
