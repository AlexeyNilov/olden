from dataclasses import dataclass

from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord


@dataclass(frozen=True, slots=True)
class _CubeCoord:
    x: int
    y: int
    z: int


def distance_between(battlefield: Battlefield, start: HexCoord, end: HexCoord) -> int:
    battlefield.require_valid(start)
    battlefield.require_valid(end)
    start_cube = _to_cube(start)
    end_cube = _to_cube(end)

    return max(
        abs(start_cube.x - end_cube.x),
        abs(start_cube.y - end_cube.y),
        abs(start_cube.z - end_cube.z),
    )


def movement_radius(battlefield: Battlefield, origin: HexCoord, speed: int) -> frozenset[HexCoord]:
    if speed < 0:
        msg = "Movement speed cannot be negative"
        raise ValueError(msg)

    battlefield.require_valid(origin)
    return frozenset(coord for coord in battlefield.coordinates() if distance_between(battlefield, origin, coord) <= speed)


def _to_cube(coord: HexCoord) -> _CubeCoord:
    x = coord.column - ((coord.row + (coord.row & 1)) // 2)
    z = coord.row
    y = -x - z
    return _CubeCoord(x=x, y=y, z=z)
