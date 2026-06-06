from olden.combat.coordinates import HexCoord
from olden.combat.sides import CombatSide

DeploymentSide = CombatSide


class DeploymentZones:
    def __init__(self, sides_by_coord: dict[HexCoord, DeploymentSide] | None = None) -> None:
        self._sides_by_coord = dict(sides_by_coord or {})

    @classmethod
    def default(cls, row_lengths: tuple[int, ...]) -> "DeploymentZones":
        sides_by_coord: dict[HexCoord, DeploymentSide] = {}
        for row, row_length in enumerate(row_lengths):
            sides_by_coord[HexCoord(0, row)] = DeploymentSide.PLAYER
            sides_by_coord[HexCoord(row_length - 1, row)] = DeploymentSide.ENEMY
        return cls(sides_by_coord)

    def side_for(self, coord: HexCoord) -> DeploymentSide | None:
        return self._sides_by_coord.get(coord)
