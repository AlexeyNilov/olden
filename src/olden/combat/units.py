from dataclasses import dataclass

from olden.combat.coordinates import HexCoord
from olden.combat.sides import CombatSide


@dataclass(frozen=True, slots=True)
class UnitFootprint:
    offsets: frozenset[HexCoord]

    def __post_init__(self) -> None:
        if not self.offsets:
            msg = "Unit footprint must include at least the anchor offset"
            raise ValueError(msg)
        if HexCoord(0, 0) not in self.offsets:
            msg = "Unit footprint must include the anchor offset"
            raise ValueError(msg)

    @classmethod
    def single_hex(cls) -> "UnitFootprint":
        return cls(offsets=frozenset({HexCoord(0, 0)}))

    def coordinates_anchored_at(self, anchor: HexCoord) -> frozenset[HexCoord]:
        return frozenset(HexCoord(anchor.column + offset.column, anchor.row + offset.row) for offset in self.offsets)


@dataclass(frozen=True, slots=True)
class UnitDefinition:
    id: str
    name: str
    speed: int
    footprint: UnitFootprint

    def __post_init__(self) -> None:
        if self.speed < 0:
            msg = "Unit definition speed cannot be negative"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class UnitStack:
    id: str
    definition: UnitDefinition
    side: CombatSide
    count: int

    def __post_init__(self) -> None:
        if self.count <= 0:
            msg = "Unit stack count must be positive"
            raise ValueError(msg)
