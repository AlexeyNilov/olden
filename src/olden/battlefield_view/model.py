from collections.abc import Mapping
from dataclasses import dataclass

from olden.battlefield_view.layout import BattlefieldLayout, HexPoint, HexPosition
from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.units import UnitStack


@dataclass(frozen=True, slots=True)
class RenderableHex:
    coord: HexCoord
    center_x: float
    center_y: float
    points: tuple[HexPoint, ...]
    deployment_side: CombatSide | None
    is_blocked: bool
    occupant_id: str | None
    unit_stack: UnitStack | None


class BattlefieldView:
    def __init__(self, hexes: tuple[RenderableHex, ...]) -> None:
        self.hexes = hexes
        self._hex_by_coord = {renderable_hex.coord: renderable_hex for renderable_hex in hexes}

    def hex_at(self, coord: HexCoord) -> RenderableHex:
        try:
            return self._hex_by_coord[coord]
        except KeyError as exc:
            msg = f"Coordinate is not rendered in the battlefield view: {coord}"
            raise ValueError(msg) from exc


def build_battlefield_view(
    battlefield: Battlefield,
    occupancy: Occupancy,
    unit_stacks: Mapping[str, UnitStack] | None = None,
    layout: BattlefieldLayout | None = None,
) -> BattlefieldView:
    resolved_layout = layout or BattlefieldLayout()
    resolved_unit_stacks = unit_stacks or {}
    return BattlefieldView(
        tuple(
            _renderable_hex(battlefield, occupancy, resolved_unit_stacks, position)
            for position in resolved_layout.positions_for(battlefield)
        )
    )


def _renderable_hex(
    battlefield: Battlefield,
    occupancy: Occupancy,
    unit_stacks: Mapping[str, UnitStack],
    position: HexPosition,
) -> RenderableHex:
    coord = position.coord
    occupant_id = occupancy.unit_at(coord)
    return RenderableHex(
        coord=coord,
        center_x=position.center_x,
        center_y=position.center_y,
        points=position.points,
        deployment_side=battlefield.hex_at(coord).deployment_side,
        is_blocked=battlefield.is_blocked(coord),
        occupant_id=occupant_id,
        unit_stack=unit_stacks.get(occupant_id) if occupant_id is not None else None,
    )
