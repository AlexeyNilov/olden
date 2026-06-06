from dataclasses import dataclass

from olden.combat.coordinates import HexCoord


@dataclass(frozen=True, slots=True)
class Obstacle:
    name: str
    coordinates: frozenset[HexCoord]


class ObstacleMap:
    def __init__(self, obstacles: tuple[Obstacle, ...] = ()) -> None:
        self._blocked_coordinates = frozenset(coord for obstacle in obstacles for coord in obstacle.coordinates)

    @property
    def blocked_coordinates(self) -> frozenset[HexCoord]:
        return self._blocked_coordinates

    def blocks(self, coord: HexCoord) -> bool:
        return coord in self._blocked_coordinates
