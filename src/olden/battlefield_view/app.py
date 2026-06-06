from collections.abc import Mapping
from html import escape
from importlib import import_module
from pathlib import Path
from typing import Any

from olden.battlefield_view.model import BattlefieldView, RenderableHex, build_battlefield_view
from olden.battlefield_view.unit_images import UNIT_IMAGE_ROUTE, resolve_unit_image
from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.obstacles import Obstacle
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.units import UnitDefinition, UnitStack
from olden.unit_data.packaged import load_packaged_unit_catalog

DEFAULT_UNIT_IMAGE_DIRECTORY = Path(__file__).resolve().parents[3] / "image"


def main() -> None:
    run_battlefield_view()


def run_battlefield_view(
    battlefield: Battlefield | None = None,
    occupancy: Occupancy | None = None,
    unit_stacks: Mapping[str, UnitStack] | None = None,
) -> None:
    nicegui = _load_nicegui()
    ui = getattr(nicegui, "ui")
    resolved_battlefield = battlefield if battlefield is not None else _demo_battlefield()
    resolved_occupancy = occupancy if occupancy is not None else _demo_occupancy()
    resolved_unit_stacks = unit_stacks if unit_stacks is not None else _demo_unit_stacks()
    view = build_battlefield_view(
        resolved_battlefield,
        resolved_occupancy,
        resolved_unit_stacks,
    )
    _register_unit_image_static_files(getattr(nicegui, "app"), DEFAULT_UNIT_IMAGE_DIRECTORY)
    _build_page(ui, view)
    ui.run(title="Olden Battlefield View", reload=False, show=False)


def render_battlefield_svg(
    view: BattlefieldView,
    unit_image_directory: Path = DEFAULT_UNIT_IMAGE_DIRECTORY,
) -> str:
    width, height = _svg_size(view)
    parts = [_svg_open(width, height)]
    parts.extend(_polygon(hex_data) for hex_data in view.hexes)
    for hex_data in view.hexes:
        if hex_data.occupant_id is not None:
            parts.extend(_unit_elements(hex_data, unit_image_directory))
    parts.append("</svg>")
    return "".join(parts)


def _build_page(ui: Any, view: BattlefieldView) -> None:
    ui.page_title("Olden Battlefield View")
    ui.add_css("body { background: #10131f; }")
    with ui.column().classes("w-full items-center q-pa-md"):
        ui.html(render_battlefield_svg(view), sanitize=False).classes("battlefield-view")


def _register_unit_image_static_files(nicegui_app: Any, image_directory: Path = DEFAULT_UNIT_IMAGE_DIRECTORY) -> None:
    if image_directory.is_dir():
        nicegui_app.add_static_files(UNIT_IMAGE_ROUTE, image_directory)


def _load_nicegui() -> Any:
    try:
        return import_module("nicegui")
    except ModuleNotFoundError as exc:
        msg = 'NiceGUI is required for the battlefield view. Install it with: pip install -e ".[view]"'
        raise RuntimeError(msg) from exc


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


def _unit_elements(hex_data: RenderableHex, unit_image_directory: Path) -> tuple[str, ...]:
    if hex_data.unit_stack is None:
        return (_unit_label(hex_data),)
    unit_image = resolve_unit_image(hex_data.unit_stack, unit_image_directory)
    if unit_image is None:
        return (_unit_label(hex_data),)
    return (_unit_image(hex_data, unit_image.href), _unit_count_label(hex_data))


def _unit_image(hex_data: RenderableHex, href: str) -> str:
    bounds = _hex_bounds(hex_data)
    return (
        f'<image href="{escape(href)}" x="{bounds.min_x:.2f}" y="{bounds.min_y:.2f}" width="{bounds.width:.2f}" '
        f'height="{bounds.height:.2f}" preserveAspectRatio="xMidYMid meet" />'
    )


def _unit_label(hex_data: RenderableHex) -> str:
    label = _unit_text(hex_data)
    return (
        f'<text class="unit" x="{hex_data.center_x:.2f}" y="{hex_data.center_y + 4:.2f}" '
        f'text-anchor="middle" fill="#f7f0d0" font-family="sans-serif" font-size="12" font-weight="700">{escape(label)}</text>'
    )


def _unit_count_label(hex_data: RenderableHex) -> str:
    if hex_data.unit_stack is None:
        return _unit_label(hex_data)
    bounds = _hex_bounds(hex_data)
    return (
        f'<text class="unit" x="{hex_data.center_x:.2f}" y="{bounds.max_y - 7:.2f}" '
        'text-anchor="middle" fill="#f7f0d0" stroke="#111111" stroke-width="2" paint-order="stroke" '
        'font-family="sans-serif" font-size="12" font-weight="700">'
        f"{hex_data.unit_stack.count}</text>"
    )


def _unit_text(hex_data: RenderableHex) -> str:
    if hex_data.unit_stack is None:
        return hex_data.occupant_id or ""
    return f"{hex_data.unit_stack.definition.name} {hex_data.unit_stack.count}"


class _HexBounds:
    def __init__(self, min_x: float, min_y: float, max_y: float, width: float, height: float) -> None:
        self.min_x = min_x
        self.min_y = min_y
        self.max_y = max_y
        self.width = width
        self.height = height


def _hex_bounds(hex_data: RenderableHex) -> _HexBounds:
    min_x = min(point.x for point in hex_data.points)
    max_x = max(point.x for point in hex_data.points)
    min_y = min(point.y for point in hex_data.points)
    max_y = max(point.y for point in hex_data.points)
    return _HexBounds(min_x=min_x, min_y=min_y, max_y=max_y, width=max_x - min_x, height=max_y - min_y)


def _demo_battlefield() -> Battlefield:
    obstacle = Obstacle(name="rocks", coordinates=_demo_obstacle_coordinates())
    return Battlefield.default(obstacles=(obstacle,))


def _demo_unit_stacks() -> dict[str, UnitStack]:
    definition = load_packaged_unit_catalog().get("esquire").to_unit_definition()
    return {
        "player-esquire": _demo_stack("player-esquire", definition, CombatSide.PLAYER, 10),
        "enemy-esquire": _demo_stack("enemy-esquire", definition, CombatSide.ENEMY, 20),
    }


def _demo_stack(stack_id: str, definition: UnitDefinition, side: CombatSide, count: int) -> UnitStack:
    return UnitStack(id=stack_id, definition=definition, side=side, count=count)


def _demo_occupancy() -> Occupancy:
    occupancy = Occupancy(blocked_coordinates=_demo_obstacle_coordinates())
    occupancy.place("player-esquire", HexCoord(0, 5))
    occupancy.place("enemy-esquire", HexCoord(12, 5))
    return occupancy


def _demo_obstacle_coordinates() -> frozenset[HexCoord]:
    return frozenset({HexCoord(5, 4), HexCoord(9, 3), HexCoord(2, 6)})


if __name__ == "__main__":
    main()
