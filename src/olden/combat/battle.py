from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.heroes import Hero
from olden.combat.movement import validate_movement
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.units import UnitStack

if TYPE_CHECKING:
    from olden.combat.attack import DamageChooser, MeleeAttackResult, RangedAttackResult


class UnknownUnitStackError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class MovementResult:
    stack_id: str
    start: HexCoord
    destination: HexCoord
    path: tuple[HexCoord, ...]


@dataclass(slots=True)
class Battle:
    battlefield: Battlefield
    occupancy: Occupancy
    unit_stacks: dict[str, UnitStack]
    heroes: dict[CombatSide, Hero] = field(default_factory=dict)

    def move_stack(self, stack_id: str, destination: HexCoord) -> MovementResult:
        stack = self.stack(stack_id)
        start = self._single_occupied_coordinate(stack_id)
        path = validate_movement(
            battlefield=self.battlefield,
            occupancy=self.occupancy,
            start=start,
            destination=destination,
            speed=stack.definition.speed,
            moving_unit_id=stack_id,
        )
        self.occupancy.move(stack_id, destination)
        return MovementResult(stack_id=stack_id, start=start, destination=destination, path=path)

    def attack_stack(
        self,
        attacker_id: str,
        defender_id: str,
        damage_chooser: "DamageChooser",
        allow_counterattack: bool = True,
    ) -> "MeleeAttackResult":
        from olden.combat.attack import resolve_melee_attack

        return resolve_melee_attack(self, attacker_id, defender_id, damage_chooser, allow_counterattack)

    def ranged_attack_stack(
        self,
        attacker_id: str,
        defender_id: str,
        damage_chooser: "DamageChooser",
    ) -> "RangedAttackResult":
        from olden.combat.attack import resolve_ranged_attack

        return resolve_ranged_attack(self, attacker_id, defender_id, damage_chooser)

    def stack(self, stack_id: str) -> UnitStack:
        try:
            return self.unit_stacks[stack_id]
        except KeyError as exc:
            msg = f"Unknown unit stack: {stack_id}"
            raise UnknownUnitStackError(msg) from exc

    def copy(self) -> "Battle":
        occupancy = Occupancy(blocked_coordinates=self.battlefield.blocked_coordinates)
        for stack_id in self.unit_stacks:
            coord = self.occupancy.coordinate_for(stack_id)
            if coord is not None:
                occupancy.place(stack_id, coord)
        return Battle(
            battlefield=self.battlefield,
            occupancy=occupancy,
            unit_stacks=dict(self.unit_stacks),
            heroes=dict(self.heroes),
        )

    def _single_occupied_coordinate(self, stack_id: str) -> HexCoord:
        coord = self.occupancy.coordinate_for(stack_id)
        if coord is None:
            msg = f"Expected one occupied coordinate for unit stack: {stack_id}"
            raise ValueError(msg)
        return coord
