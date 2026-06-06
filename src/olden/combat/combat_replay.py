from dataclasses import dataclass

from olden.combat.battle import Battle
from olden.combat.combat_log import (
    BattleStartedEvent,
    CombatLog,
    CombatLogEvent,
    CombatLogValidationError,
    UnitMovedEvent,
)


@dataclass(frozen=True, slots=True)
class CombatReplayFrame:
    battle: Battle
    event: CombatLogEvent | None
    index: int
    total: int


def build_combat_replay_frames(initial_battle: Battle, combat_log: CombatLog) -> tuple[CombatReplayFrame, ...]:
    battle = initial_battle.copy()
    frame_data: list[tuple[Battle, CombatLogEvent | None]] = [(battle.copy(), None)]
    for event in combat_log.events:
        if isinstance(event, BattleStartedEvent):
            continue
        _apply_unit_moved_event(battle, event)
        frame_data.append((battle.copy(), event))

    total = len(frame_data)
    return tuple(
        CombatReplayFrame(
            battle=frame_battle,
            event=event,
            index=index,
            total=total,
        )
        for index, (frame_battle, event) in enumerate(frame_data)
    )


def _apply_unit_moved_event(battle: Battle, event: UnitMovedEvent) -> None:
    movement = battle.move_stack(event.stack_id, event.destination)
    if movement.start != event.start or movement.path != event.path:
        msg = f"Combat log movement does not match replayed movement for unit stack: {event.stack_id}"
        raise CombatLogValidationError(msg)
