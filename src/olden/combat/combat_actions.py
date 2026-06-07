from olden.combat.action_opportunities import CombatRoundState
from olden.combat.attack import DamageChooser
from olden.combat.battle import Battle
from olden.combat.combat_log import (
    CombatLog,
    CombatLogReplayState,
    CombatLogValidationError,
    TurnMarker,
    UnitAttackedEvent,
    UnitMovedEvent,
    UnitSkippedEvent,
    UnitWaitedEvent,
    snapshot_attack_damage,
)
from olden.combat.coordinates import HexCoord
from olden.combat.units import DamageRange


def apply_movement_action(
    battle: Battle,
    combat_log: CombatLog,
    turn: TurnMarker,
    stack_id: str,
    destination: HexCoord,
) -> UnitMovedEvent:
    movement = battle.move_stack(stack_id, destination)
    return combat_log.record_unit_moved(turn, movement)


def apply_melee_attack_action(
    battle: Battle,
    combat_log: CombatLog,
    turn: TurnMarker,
    attacker_id: str,
    defender_id: str,
    damage_chooser: DamageChooser,
    round_state: CombatRoundState,
) -> UnitAttackedEvent:
    attack = battle.attack_stack(
        attacker_id,
        defender_id,
        damage_chooser,
        allow_counterattack=round_state.can_counterattack(defender_id),
    )
    if attack.counterattack is not None:
        round_state.record_counterattack(defender_id)
    return combat_log.record_unit_attacked(turn, attack)


def apply_wait_action(combat_log: CombatLog, turn: TurnMarker, stack_id: str) -> UnitWaitedEvent:
    return combat_log.record_unit_waited(turn, stack_id)


def apply_skip_action(combat_log: CombatLog, turn: TurnMarker, stack_id: str) -> UnitSkippedEvent:
    return combat_log.record_unit_skipped(turn, stack_id)


def apply_logged_movement_action(battle: Battle, event: UnitMovedEvent) -> None:
    movement = battle.move_stack(event.stack_id, event.destination)
    if movement.start != event.start or movement.path != event.path:
        msg = f"Combat log movement does not match replayed movement for unit stack: {event.stack_id}"
        raise CombatLogValidationError(msg)


def apply_logged_melee_attack_action(
    battle: Battle,
    event: UnitAttackedEvent,
    replay_state: CombatLogReplayState,
) -> None:
    selected_damages = [event.primary_damage.selected_damage]
    if event.counterattack is not None:
        selected_damages.append(event.counterattack.selected_damage)
    selected_damage_index = 0

    def choose_logged_damage(_: DamageRange) -> int:
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
        allow_counterattack=counterattack_key not in replay_state.counterattacked_stack_ids_by_round,
    )
    if snapshot_attack_damage(attack.primary_damage) != event.primary_damage:
        msg = f"Combat log attack does not match replayed primary damage for unit stack: {event.attacker_id}"
        raise CombatLogValidationError(msg)
    replayed_counterattack = snapshot_attack_damage(attack.counterattack) if attack.counterattack is not None else None
    if replayed_counterattack != event.counterattack:
        msg = f"Combat log attack does not match replayed counterattack damage for unit stack: {event.attacker_id}"
        raise CombatLogValidationError(msg)
    if attack.counterattack is not None:
        replay_state.counterattacked_stack_ids_by_round.add(counterattack_key)
