from dataclasses import dataclass, field

from olden.combat.combat_log import TurnMarker


@dataclass(slots=True)
class CombatRoundState:
    round_number: int
    counterattacked_stack_ids: set[str] = field(default_factory=set)
    waited_stack_ids: set[str] = field(default_factory=set)
    waiting_stack_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.round_number < 1:
            msg = "Round number must be positive"
            raise ValueError(msg)

    def turn_marker(self, turn_number: int) -> TurnMarker:
        return TurnMarker(round_number=self.round_number, turn_number=turn_number)

    def can_counterattack(self, stack_id: str) -> bool:
        return stack_id not in self.counterattacked_stack_ids

    def record_counterattack(self, stack_id: str) -> None:
        self.counterattacked_stack_ids.add(stack_id)

    def has_counterattacked(self, stack_id: str) -> bool:
        return stack_id in self.counterattacked_stack_ids

    def can_wait(self, stack_id: str) -> bool:
        return stack_id not in self.waited_stack_ids

    def record_wait(self, stack_id: str) -> None:
        self.waited_stack_ids.add(stack_id)
        self.waiting_stack_ids.append(stack_id)

    def waited_stacks(self) -> tuple[str, ...]:
        return tuple(self.waiting_stack_ids)
