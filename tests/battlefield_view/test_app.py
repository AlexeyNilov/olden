from olden.battlefield_view.app import _build_page, _demo_battle, _register_unit_image_static_files, render_battlefield_svg
from olden.battlefield_view.model import build_battlefield_view
from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.units import UnitDefinition, UnitFootprint, UnitStack


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


def test_svg_renderer_uses_unit_image_and_count_label_when_definition_image_exists(tmp_path):
    stack = _stack_for_unit("player-esquire", "esquire", "Swordsman", 10)
    occupancy = Occupancy()
    occupancy.place(stack.id, HexCoord(4, 5))
    (tmp_path / "esquire.webp").write_bytes(b"image")
    view = build_battlefield_view(Battlefield.default(), occupancy, unit_stacks={stack.id: stack})

    svg = render_battlefield_svg(view, unit_image_directory=tmp_path)

    assert '<image href="/unit-images/esquire.webp"' in svg
    assert ">10</text>" in svg
    assert "Swordsman 10" not in svg


def test_svg_renderer_sizes_unit_image_to_fill_the_hex_bounds(tmp_path):
    stack = _stack_for_unit("player-esquire", "esquire", "Swordsman", 10)
    occupancy = Occupancy()
    occupancy.place(stack.id, HexCoord(4, 5))
    (tmp_path / "esquire.webp").write_bytes(b"image")
    view = build_battlefield_view(Battlefield.default(), occupancy, unit_stacks={stack.id: stack})
    hex_data = view.hex_at(HexCoord(4, 5))
    min_x = min(point.x for point in hex_data.points)
    max_x = max(point.x for point in hex_data.points)
    min_y = min(point.y for point in hex_data.points)
    max_y = max(point.y for point in hex_data.points)

    svg = render_battlefield_svg(view, unit_image_directory=tmp_path)

    assert f'x="{min_x:.2f}"' in svg
    assert f'y="{min_y:.2f}"' in svg
    assert f'width="{max_x - min_x:.2f}"' in svg
    assert f'height="{max_y - min_y:.2f}"' in svg


def test_svg_renderer_places_unit_image_count_near_the_bottom_of_the_hex(tmp_path):
    stack = _stack_for_unit("player-esquire", "esquire", "Swordsman", 10)
    occupancy = Occupancy()
    occupancy.place(stack.id, HexCoord(4, 5))
    (tmp_path / "esquire.webp").write_bytes(b"image")
    view = build_battlefield_view(Battlefield.default(), occupancy, unit_stacks={stack.id: stack})
    hex_data = view.hex_at(HexCoord(4, 5))
    max_y = max(point.y for point in hex_data.points)

    svg = render_battlefield_svg(view, unit_image_directory=tmp_path)

    assert f'y="{max_y - 7:.2f}"' in svg


def test_svg_renderer_falls_back_to_unit_name_and_count_when_definition_image_is_missing(tmp_path):
    stack = _stack_for_unit("player-esquire", "esquire", "Swordsman", 10)
    occupancy = Occupancy()
    occupancy.place(stack.id, HexCoord(4, 5))
    view = build_battlefield_view(Battlefield.default(), occupancy, unit_stacks={stack.id: stack})

    svg = render_battlefield_svg(view, unit_image_directory=tmp_path)

    assert "<image " not in svg
    assert "Swordsman 10" in svg


def test_nicegui_page_embeds_trusted_generated_svg_without_sanitizing():
    ui = FakeUi()
    view = build_battlefield_view(Battlefield.default(), Occupancy())

    _build_page(ui, view)

    assert ui.html_sanitize is False


def test_register_unit_image_static_files_uses_local_image_directory(tmp_path):
    app = FakeApp()

    _register_unit_image_static_files(app, tmp_path)

    assert app.static_files == [("/unit-images", tmp_path)]


def test_demo_battle_loads_state_from_demo_battle_yaml():
    battle = _demo_battle()

    assert battle.battlefield.is_blocked(HexCoord(5, 4))
    assert battle.occupancy.unit_at(HexCoord(0, 9)) == "player-esquire"
    assert battle.occupancy.unit_at(HexCoord(12, 5)) == "enemy-esquire"
    assert battle.unit_stacks["player-esquire"].definition.id == "esquire"
    assert battle.unit_stacks["player-esquire"].definition.name == "Swordsman"


def _stack_for_unit(stack_id: str, unit_id: str, name: str, count: int) -> UnitStack:
    definition = UnitDefinition(id=unit_id, name=name, speed=4, footprint=UnitFootprint.single_hex())
    return UnitStack(id=stack_id, definition=definition, side=CombatSide.PLAYER, count=count)


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


class FakeApp:
    def __init__(self) -> None:
        self.static_files: list[tuple[str, object]] = []

    def add_static_files(self, url_path: str, local_directory: object) -> None:
        self.static_files.append((url_path, local_directory))


class FakeElement:
    def classes(self, classes: str) -> "FakeElement":
        return self

    def __enter__(self) -> "FakeElement":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        pass
