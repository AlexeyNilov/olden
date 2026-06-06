from collections.abc import Iterator
from dataclasses import dataclass

from olden.combat.coordinates import DEFAULT_ROW_LENGTHS, HexCoord
from olden.combat.deployment import DeploymentSide, DeploymentZones
from olden.combat.obstacles import Obstacle, ObstacleMap


@dataclass(frozen=True, slots=True)
class BattlefieldHex:
    coord: HexCoord
    deployment_side: DeploymentSide | None


class Battlefield:
    def __init__(
        self,
        row_lengths: tuple[int, ...] = DEFAULT_ROW_LENGTHS,
        deployment_zones: DeploymentZones | None = None,
        obstacles: tuple[Obstacle, ...] = (),
    ) -> None:
        self.row_lengths = row_lengths
        self._deployment_zones = deployment_zones or DeploymentZones.default(row_lengths)
        self._obstacles = ObstacleMap(obstacles)

    @classmethod
    def default(cls, obstacles: tuple[Obstacle, ...] = ()) -> "Battlefield":
        return cls(obstacles=obstacles)

    def coordinates(self) -> Iterator[HexCoord]:
        for row, row_length in enumerate(self.row_lengths):
            for column in range(row_length):
                yield HexCoord(column, row)

    def contains(self, coord: HexCoord) -> bool:
        if coord.row < 0 or coord.row >= len(self.row_lengths):
            return False
        return 0 <= coord.column < self.row_lengths[coord.row]

    def require_valid(self, coord: HexCoord) -> None:
        if not self.contains(coord):
            msg = f"Invalid battlefield coordinate: {coord}"
            raise ValueError(msg)

    def neighbors(self, coord: HexCoord) -> tuple[HexCoord, ...]:
        self.require_valid(coord)
        return tuple(candidate for candidate in self._neighbor_candidates(coord) if self.contains(candidate))

    def hex_at(self, coord: HexCoord) -> BattlefieldHex:
        self.require_valid(coord)
        return BattlefieldHex(coord=coord, deployment_side=self._deployment_zones.side_for(coord))

    def is_blocked(self, coord: HexCoord) -> bool:
        self.require_valid(coord)
        return self._obstacles.blocks(coord)

    def _neighbor_candidates(self, coord: HexCoord) -> tuple[HexCoord, ...]:
        column = coord.column
        row = coord.row
        if row % 2 == 0:
            return self._even_row_neighbor_candidates(column, row)
        return self._odd_row_neighbor_candidates(column, row)

    @staticmethod
    def _even_row_neighbor_candidates(column: int, row: int) -> tuple[HexCoord, ...]:
        return (
            HexCoord(column - 1, row),
            HexCoord(column + 1, row),
            HexCoord(column, row - 1),
            HexCoord(column + 1, row - 1),
            HexCoord(column, row + 1),
            HexCoord(column + 1, row + 1),
        )

    @staticmethod
    def _odd_row_neighbor_candidates(column: int, row: int) -> tuple[HexCoord, ...]:
        return (
            HexCoord(column - 1, row),
            HexCoord(column + 1, row),
            HexCoord(column - 1, row - 1),
            HexCoord(column, row - 1),
            HexCoord(column - 1, row + 1),
            HexCoord(column, row + 1),
        )
