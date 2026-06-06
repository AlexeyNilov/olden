from collections.abc import Iterator
from dataclasses import dataclass
from math import cos, pi, sin, sqrt

from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord


@dataclass(frozen=True, slots=True)
class HexPoint:
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class HexPosition:
    coord: HexCoord
    center_x: float
    center_y: float
    points: tuple[HexPoint, ...]


@dataclass(frozen=True, slots=True)
class BattlefieldLayout:
    hex_radius: float = 32.0

    @property
    def horizontal_step(self) -> float:
        return self.hex_radius * 1.5

    @property
    def vertical_step(self) -> float:
        return self.hex_radius * sqrt(3) / 2

    def positions_for(self, battlefield: Battlefield) -> tuple[HexPosition, ...]:
        return tuple(self.position_for(coord) for coord in battlefield.coordinates())

    def position_for(self, coord: HexCoord) -> HexPosition:
        center_x = self._center_x(coord)
        center_y = self.hex_radius * sqrt(3) / 2 + coord.row * self.vertical_step
        return HexPosition(coord=coord, center_x=center_x, center_y=center_y, points=tuple(self._points(center_x, center_y)))

    def _center_x(self, coord: HexCoord) -> float:
        origin_x = self.hex_radius + self.horizontal_step / 2
        row_offset = -self.horizontal_step / 2 if coord.row % 2 else 0
        return origin_x + coord.column * self.horizontal_step + row_offset

    def _points(self, center_x: float, center_y: float) -> Iterator[HexPoint]:
        for index in range(6):
            angle = pi / 3 * index
            yield HexPoint(x=center_x + self.hex_radius * cos(angle), y=center_y + self.hex_radius * sin(angle))
