from dataclasses import dataclass

from olden.combat.battle import Battle
from olden.combat.combat_log import (
    CombatLog,
    CombatLogEvent,
    CombatLogReplayState,
    apply_combat_log_event,
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
    replay_state = CombatLogReplayState()
    for event in combat_log.events:
        if apply_combat_log_event(battle, event, replay_state):
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
