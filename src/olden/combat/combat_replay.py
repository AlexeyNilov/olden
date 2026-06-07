from dataclasses import dataclass

from olden.combat.attack import AttackDamageResult
from olden.combat.battle import Battle
from olden.combat.combat_log import (
    AttackDamageEventData,
    BattleStartedEvent,
    CombatLog,
    CombatLogEvent,
    CombatLogValidationError,
    UnitAttackedEvent,
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
    counterattacked_stack_ids_by_round: set[tuple[int, str]] = set()
    for event in combat_log.events:
        if isinstance(event, BattleStartedEvent):
            continue
        if isinstance(event, UnitMovedEvent):
            _apply_unit_moved_event(battle, event)
        else:
            _apply_unit_attacked_event(battle, event, counterattacked_stack_ids_by_round)
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


def _apply_unit_attacked_event(
    battle: Battle,
    event: UnitAttackedEvent,
    counterattacked_stack_ids_by_round: set[tuple[int, str]],
) -> None:
    selected_damages = [event.primary_damage.selected_damage]
    if event.counterattack is not None:
        selected_damages.append(event.counterattack.selected_damage)
    selected_damage_index = 0

    def choose_logged_damage(_: object) -> int:
        nonlocal selected_damage_index
        if selected_damage_index >= len(selected_damages):
            msg = f"Combat log attack is missing replayed damage for unit stack: {event.attacker_id}"
            raise CombatLogValidationError(msg)
        selected_damage = selected_damages[selected_damage_index]
        selected_damage_index += 1
        return selected_damage

    counterattack_key = (event.turn.round_number, event.defender_id)
    attack = battle.attack_stack(
        event.attacker_id,
        event.defender_id,
        choose_logged_damage,
        allow_counterattack=counterattack_key not in counterattacked_stack_ids_by_round,
    )
    if not _damage_matches_event(attack.primary_damage, event.primary_damage):
        msg = f"Combat log attack does not match replayed primary damage for unit stack: {event.attacker_id}"
        raise CombatLogValidationError(msg)
    if attack.counterattack is None:
        replayed_counterattack_matches = event.counterattack is None
    else:
        replayed_counterattack_matches = event.counterattack is not None and _damage_matches_event(
            attack.counterattack,
            event.counterattack,
        )
    if not replayed_counterattack_matches:
        msg = f"Combat log attack does not match replayed counterattack damage for unit stack: {event.attacker_id}"
        raise CombatLogValidationError(msg)
    if attack.counterattack is not None:
        counterattacked_stack_ids_by_round.add(counterattack_key)


def _damage_matches_event(attack_damage: AttackDamageResult, event_damage: AttackDamageEventData) -> bool:
    return (
        attack_damage.selected_damage == event_damage.selected_damage
        and attack_damage.final_damage == event_damage.final_damage
        and attack_damage.creatures_killed == event_damage.creatures_killed
        and attack_damage.defender_count_before == event_damage.defender_count_before
        and attack_damage.defender_count_after == event_damage.defender_count_after
        and attack_damage.defender_wound_damage_after == event_damage.defender_wound_damage_after
        and attack_damage.defender_defeated == event_damage.defender_defeated
    )
