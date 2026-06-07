from olden.battlefield_view.model import build_battlefield_view
from olden.battlefield_view.svg import register_unit_image_static_files, render_battlefield_svg
from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.units import AttackCategory, DamageRange, UnitCombatStats, UnitDefinition, UnitFootprint, UnitStack


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
    assert 'class="unit-side player"' in svg
    assert ">P</text>" in svg


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
    assert 'class="unit-side player"' in svg


def test_svg_renderer_marks_enemy_unit_stacks_with_enemy_side_badge(tmp_path):
    stack = UnitStack(
        id="enemy-esquire",
        definition=UnitDefinition(
            id="esquire",
            name="Swordsman",
            initiative=5,
            speed=4,
            footprint=UnitFootprint.single_hex(),
            combat=_combat_stats(),
        ),
        side=CombatSide.ENEMY,
        count=20,
    )
    occupancy = Occupancy()
    occupancy.place(stack.id, HexCoord(8, 5))
    view = build_battlefield_view(Battlefield.default(), occupancy, unit_stacks={stack.id: stack})

    svg = render_battlefield_svg(view, unit_image_directory=tmp_path)

    assert 'class="unit-side enemy"' in svg
    assert ">E</text>" in svg


def test_register_unit_image_static_files_uses_local_image_directory(tmp_path):
    app = FakeApp()

    register_unit_image_static_files(app, tmp_path)

    assert app.static_files == [("/unit-images", tmp_path)]


def _stack_for_unit(stack_id: str, unit_id: str, name: str, count: int) -> UnitStack:
    definition = UnitDefinition(
        id=unit_id,
        name=name,
        initiative=5,
        speed=4,
        footprint=UnitFootprint.single_hex(),
        combat=_combat_stats(),
    )
    return UnitStack(id=stack_id, definition=definition, side=CombatSide.PLAYER, count=count)


def _combat_stats() -> UnitCombatStats:
    return UnitCombatStats(
        health=12,
        attack=4,
        defense=4,
        damage=DamageRange(minimum=2, maximum=3),
        attack_category=AttackCategory.MELEE,
    )


class FakeApp:
    def __init__(self) -> None:
        self.static_files: list[tuple[str, object]] = []

    def add_static_files(self, url_path: str, local_directory: object) -> None:
        self.static_files.append((url_path, local_directory))
