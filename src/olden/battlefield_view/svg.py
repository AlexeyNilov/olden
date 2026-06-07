from html import escape
from pathlib import Path
from typing import Any

from olden.battlefield_view.model import BattlefieldView, RenderableHex
from olden.battlefield_view.unit_images import UNIT_IMAGE_ROUTE, resolve_unit_image
from olden.combat.sides import CombatSide

DEFAULT_UNIT_IMAGE_DIRECTORY = Path(__file__).resolve().parents[3] / "image"


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


def register_unit_image_static_files(nicegui_app: Any, image_directory: Path = DEFAULT_UNIT_IMAGE_DIRECTORY) -> None:
    if image_directory.is_dir():
        nicegui_app.add_static_files(UNIT_IMAGE_ROUTE, image_directory)


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
    if hex_data.deployment_side is CombatSide.ATTACKER:
        classes.append("attacker")
    if hex_data.deployment_side is CombatSide.DEFENDER:
        classes.append("defender")
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
    if hex_data.deployment_side is CombatSide.ATTACKER:
        return "#3f6fa8"
    if hex_data.deployment_side is CombatSide.DEFENDER:
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
        return (_unit_label(hex_data), _unit_side_badge(hex_data))
    return (_unit_image(hex_data, unit_image.href), _unit_count_label(hex_data), _unit_side_badge(hex_data))


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


def _unit_side_badge(hex_data: RenderableHex) -> str:
    if hex_data.unit_stack is None:
        return ""
    bounds = _hex_bounds(hex_data)
    radius = 9
    center_x = bounds.min_x + radius + 3
    center_y = bounds.min_y + radius + 3
    side = hex_data.unit_stack.side
    marker = "A" if side is CombatSide.ATTACKER else "D"
    return (
        f'<circle class="unit-side {side.value}" cx="{center_x:.2f}" cy="{center_y:.2f}" r="{radius}" '
        f'fill="{_unit_side_fill(side)}" stroke="#111111" stroke-width="2" />'
        f'<text class="unit-side {side.value}" x="{center_x:.2f}" y="{center_y + 4:.2f}" text-anchor="middle" '
        f'fill="#ffffff" stroke="#111111" stroke-width="1" paint-order="stroke" '
        f'font-family="sans-serif" font-size="12" font-weight="800">{marker}</text>'
    )


def _unit_side_fill(side: CombatSide) -> str:
    if side is CombatSide.ATTACKER:
        return "#2f80d0"
    return "#c6534a"


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
