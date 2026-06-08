from dataclasses import dataclass
from enum import Enum

from olden.combat.sides import CombatSide


class AttackCategory(Enum):
    MELEE = "melee"
    RANGED = "ranged"


@dataclass(frozen=True, slots=True)
class DamageRange:
    minimum: int
    maximum: int

    def __post_init__(self) -> None:
        if self.minimum < 0:
            msg = "damage range minimum cannot be negative"
            raise ValueError(msg)
        if self.maximum < self.minimum:
            msg = "damage range maximum must be greater than or equal to minimum"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class UnitCombatStats:
    health: int
    attack: int
    defense: int
    damage: DamageRange
    attack_category: AttackCategory

    def __post_init__(self) -> None:
        if self.health <= 0:
            msg = "Unit combat health must be positive"
            raise ValueError(msg)
        if self.attack < 0:
            msg = "Unit combat attack cannot be negative"
            raise ValueError(msg)
        if self.defense < 0:
            msg = "Unit combat defense cannot be negative"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class UnitDefinition:
    id: str
    name: str
    initiative: int
    speed: int
    combat: UnitCombatStats

    def __post_init__(self) -> None:
        if self.initiative < 0:
            msg = "Unit definition initiative cannot be negative"
            raise ValueError(msg)
        if self.speed < 0:
            msg = "Unit definition speed cannot be negative"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class UnitStack:
    id: str
    definition: UnitDefinition
    side: CombatSide
    count: int
    wound_damage: int = 0

    def __post_init__(self) -> None:
        if self.count <= 0:
            msg = "Unit stack count must be positive"
            raise ValueError(msg)
        if self.wound_damage < 0:
            msg = "Unit stack wound damage cannot be negative"
            raise ValueError(msg)
        if self.wound_damage >= self.definition.combat.health:
            msg = "Unit stack wound damage must be lower than unit health"
            raise ValueError(msg)
