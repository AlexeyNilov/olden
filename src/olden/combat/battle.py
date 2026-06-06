from dataclasses import dataclass

from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.movement import validate_movement
from olden.combat.occupancy import Occupancy
from olden.combat.units import UnitStack


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

    def stack(self, stack_id: str) -> UnitStack:
        try:
            return self.unit_stacks[stack_id]
        except KeyError as exc:
            msg = f"Unknown unit stack: {stack_id}"
            raise UnknownUnitStackError(msg) from exc

    def copy(self) -> "Battle":
        occupancy = Occupancy(blocked_coordinates=self.battlefield.blocked_coordinates)
        for stack_id in self.unit_stacks:
            for coord in self.occupancy.coordinates_for(stack_id):
                occupancy.place(stack_id, coord)
        return Battle(
            battlefield=self.battlefield,
            occupancy=occupancy,
            unit_stacks=dict(self.unit_stacks),
        )

    def _single_occupied_coordinate(self, stack_id: str) -> HexCoord:
        coordinates = self.occupancy.coordinates_for(stack_id)
        if len(coordinates) != 1:
            msg = f"Expected one occupied coordinate for unit stack: {stack_id}"
            raise ValueError(msg)
        return next(iter(coordinates))
