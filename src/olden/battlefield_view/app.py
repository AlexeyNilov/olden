from collections.abc import Mapping
from html import escape
from importlib import import_module
from typing import Any

from olden.battlefield_view.model import BattlefieldView, RenderableHex, build_battlefield_view
from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.obstacles import Obstacle
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.units import UnitDefinition, UnitFootprint, UnitStack


def main() -> None:
    run_battlefield_view()


def run_battlefield_view(
    battlefield: Battlefield | None = None,
    occupancy: Occupancy | None = None,
    unit_stacks: Mapping[str, UnitStack] | None = None,
) -> None:
    ui = _load_nicegui_ui()
    resolved_battlefield = battlefield if battlefield is not None else _demo_battlefield()
    resolved_occupancy = occupancy if occupancy is not None else _demo_occupancy()
    resolved_unit_stacks = unit_stacks if unit_stacks is not None else _demo_unit_stacks()
    view = build_battlefield_view(
        resolved_battlefield,
        resolved_occupancy,
        resolved_unit_stacks,
    )
    _build_page(ui, view)
    ui.run(title="Olden Battlefield View", reload=False, show=False)


def render_battlefield_svg(view: BattlefieldView) -> str:
    width, height = _svg_size(view)
    parts = [_svg_open(width, height)]
    parts.extend(_polygon(hex_data) for hex_data in view.hexes)
    parts.extend(_unit_label(hex_data) for hex_data in view.hexes if hex_data.occupant_id is not None)
    parts.append("</svg>")
    return "".join(parts)


def _build_page(ui: Any, view: BattlefieldView) -> None:
    ui.page_title("Olden Battlefield View")
    ui.add_css("body { background: #10131f; }")
    with ui.column().classes("w-full items-center q-pa-md"):
        ui.html(render_battlefield_svg(view), sanitize=False).classes("battlefield-view")


def _load_nicegui_ui() -> Any:
    try:
        nicegui = import_module("nicegui")
    except ModuleNotFoundError as exc:
        msg = 'NiceGUI is required for the battlefield view. Install it with: pip install -e ".[view]"'
        raise RuntimeError(msg) from exc
    return getattr(nicegui, "ui")


def _svg_open(width: float, height: float) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.2f} {height:.2f}" '
        f'width="{width:.2f}" height="{height:.2f}" role="img" aria-label="Olden battlefield" '
        'style="display: block; max-width: 100%; height: auto;">'
    )


def _svg_size(view: BattlefieldView) -> tuple[float, float]:
    max_x = max(point.x for hex_data in view.hexes for point in hex_data.points)
    max_y = max(point.y for hex_data in view.hexes for point in hex_data.points)
    return max_x + 16, max_y + 16


def _polygon(hex_data: RenderableHex) -> str:
    return (
        f'<polygon class="{_hex_classes(hex_data)}" points="{_points(hex_data)}" fill="{_hex_fill(hex_data)}" '
        f'stroke="{_hex_stroke(hex_data)}" stroke-width="{_hex_stroke_width(hex_data)}">'
        f"<title>{_title(hex_data)}</title></polygon>"
    )


def _hex_classes(hex_data: RenderableHex) -> str:
    classes = ["hex"]
    if hex_data.deployment_side is CombatSide.PLAYER:
        classes.append("player")
    if hex_data.deployment_side is CombatSide.ENEMY:
        classes.append("enemy")
    if hex_data.is_blocked:
        classes.append("blocked")
    if hex_data.occupant_id is not None:
        classes.append("occupied")
    return " ".join(classes)


def _points(hex_data: RenderableHex) -> str:
    return " ".join(f"{point.x:.2f},{point.y:.2f}" for point in hex_data.points)


def _hex_fill(hex_data: RenderableHex) -> str:
    if hex_data.is_blocked:
        return "#3a3a34"
    if hex_data.deployment_side is CombatSide.PLAYER:
        return "#3f6fa8"
    if hex_data.deployment_side is CombatSide.ENEMY:
        return "#9a4f46"
    return "#556b3d"


def _hex_stroke(hex_data: RenderableHex) -> str:
    if hex_data.occupant_id is not None:
        return "#f2d27a"
    return "#25251f"


def _hex_stroke_width(hex_data: RenderableHex) -> str:
    if hex_data.occupant_id is not None:
        return "4"
    return "3"


def _title(hex_data: RenderableHex) -> str:
    parts = [f"({hex_data.coord.column}, {hex_data.coord.row})"]
    if hex_data.deployment_side is not None:
        parts.append(hex_data.deployment_side.value)
    if hex_data.is_blocked:
        parts.append("blocked")
    if hex_data.occupant_id is not None:
        parts.append(hex_data.occupant_id)
    return escape(" - ".join(parts))


def _unit_label(hex_data: RenderableHex) -> str:
    label = _unit_text(hex_data)
    return (
        f'<text class="unit" x="{hex_data.center_x:.2f}" y="{hex_data.center_y + 4:.2f}" '
        f'text-anchor="middle" fill="#f7f0d0" font-family="sans-serif" font-size="12" font-weight="700">{escape(label)}</text>'
    )


def _unit_text(hex_data: RenderableHex) -> str:
    if hex_data.unit_stack is None:
        return hex_data.occupant_id or ""
    return f"{hex_data.unit_stack.definition.name} {hex_data.unit_stack.count}"


def _demo_battlefield() -> Battlefield:
    obstacle = Obstacle(name="rocks", coordinates=_demo_obstacle_coordinates())
    return Battlefield.default(obstacles=(obstacle,))


def _demo_unit_stacks() -> dict[str, UnitStack]:
    return {
        "swordsman": _demo_stack("swordsman", "Swordsman", CombatSide.PLAYER, 10, 4),
        "swordsman_enemy": _demo_stack("swordsman", "Swordsman", CombatSide.ENEMY, 20, 3),
    }


def _demo_stack(unit_id: str, name: str, side: CombatSide, count: int, speed: int) -> UnitStack:
    definition = UnitDefinition(id=unit_id, name=name, speed=speed, footprint=UnitFootprint.single_hex())
    return UnitStack(id=unit_id, definition=definition, side=side, count=count)


def _demo_occupancy() -> Occupancy:
    occupancy = Occupancy(blocked_coordinates=_demo_obstacle_coordinates())
    occupancy.place("swordsman", HexCoord(0, 5))
    occupancy.place("swordsman_enemy", HexCoord(12, 5))
    return occupancy


def _demo_obstacle_coordinates() -> frozenset[HexCoord]:
    return frozenset({HexCoord(5, 4), HexCoord(9, 3), HexCoord(2, 6)})


if __name__ == "__main__":
    main()
