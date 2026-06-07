import random
from dataclasses import dataclass
from enum import Enum

from olden.combat.action_opportunities import CombatRoundState
from olden.combat.attack import DamageChooser
from olden.combat.battle import Battle
from olden.combat.combat_actions import apply_melee_attack_action, apply_movement_action
from olden.combat.combat_log import CombatLog
from olden.combat.engagement import MovementPath as MovementPath
from olden.combat.engagement import PathChooser, are_adjacent, choose_engagement_path, destination_for_speed
from olden.combat.targeting import is_defeated, nearest_living_opponent, one_side_defeated
from olden.combat.turn_order import order_stacks_for_round
from olden.combat.units import DamageRange


class CombatSimulationStopReason(Enum):
    STACK_DEFEATED = "stack_defeated"
    NO_REACHABLE_ENGAGEMENT = "no_reachable_engagement"
    MAX_TURNS_REACHED = "max_turns_reached"


@dataclass(frozen=True, slots=True)
class CombatSimulationResult:
    battle: Battle
    combat_log: CombatLog
    stop_reason: CombatSimulationStopReason
    turns_taken: int


def simulate_combat(
    initial_battle: Battle,
    first_stack_id: str | None = None,
    second_stack_id: str | None = None,
    path_chooser: PathChooser = random.choice,
    damage_chooser: DamageChooser | None = None,
    max_turns: int = 50,
    stack_ids: tuple[str, ...] | None = None,
) -> CombatSimulationResult:
    if max_turns < 1:
        msg = "Maximum simulated turns must be positive"
        raise ValueError(msg)
    configured_stack_ids = _configured_stack_ids(initial_battle, first_stack_id, second_stack_id, stack_ids)

    battle = initial_battle.copy()
    combat_log = CombatLog()
    combat_log.record_battle_started()
    resolved_damage_chooser = damage_chooser or random_damage
    turns_taken = 0
    round_number = 1

    while turns_taken < max_turns:
        if one_side_defeated(battle):
            return _result(battle, combat_log, CombatSimulationStopReason.STACK_DEFEATED, turns_taken)

        round_order = order_stacks_for_round(battle, configured_stack_ids)
        round_state = CombatRoundState(round_number=round_number)
        for turn_number, actor_id in enumerate(round_order, start=1):
            if turns_taken >= max_turns:
                return _result(battle, combat_log, CombatSimulationStopReason.MAX_TURNS_REACHED, turns_taken)
            if is_defeated(battle, actor_id):
                continue
            if one_side_defeated(battle):
                return _result(battle, combat_log, CombatSimulationStopReason.STACK_DEFEATED, turns_taken)

            opponent_id = nearest_living_opponent(battle, actor_id, configured_stack_ids)
            if opponent_id is None:
                return _result(battle, combat_log, CombatSimulationStopReason.STACK_DEFEATED, turns_taken)

            turn = round_state.turn_marker(turn_number)
            if are_adjacent(battle, actor_id, opponent_id):
                apply_melee_attack_action(
                    battle,
                    combat_log,
                    turn,
                    actor_id,
                    opponent_id,
                    resolved_damage_chooser,
                    round_state,
                )
                turns_taken += 1
                if one_side_defeated(battle):
                    return _result(battle, combat_log, CombatSimulationStopReason.STACK_DEFEATED, turns_taken)
                continue

            path = choose_engagement_path(battle, actor_id, opponent_id, path_chooser)
            if path is None:
                return _result(battle, combat_log, CombatSimulationStopReason.NO_REACHABLE_ENGAGEMENT, turns_taken)

            destination = destination_for_speed(path, battle.stack(actor_id).definition.speed)
            apply_movement_action(battle, combat_log, turn, actor_id, destination)
            if are_adjacent(battle, actor_id, opponent_id):
                apply_melee_attack_action(
                    battle,
                    combat_log,
                    turn,
                    actor_id,
                    opponent_id,
                    resolved_damage_chooser,
                    round_state,
                )
            turns_taken += 1
            if one_side_defeated(battle):
                return _result(battle, combat_log, CombatSimulationStopReason.STACK_DEFEATED, turns_taken)
        round_number += 1

    return _result(battle, combat_log, CombatSimulationStopReason.MAX_TURNS_REACHED, max_turns)


def random_damage(damage: DamageRange) -> int:
    return random.randint(damage.minimum, damage.maximum)


def _result(
    battle: Battle,
    combat_log: CombatLog,
    stop_reason: CombatSimulationStopReason,
    turns_taken: int,
) -> CombatSimulationResult:
    return CombatSimulationResult(
        battle=battle,
        combat_log=combat_log,
        stop_reason=stop_reason,
        turns_taken=turns_taken,
    )


def _configured_stack_ids(
    initial_battle: Battle,
    first_stack_id: str | None,
    second_stack_id: str | None,
    stack_ids: tuple[str, ...] | None,
) -> tuple[str, ...]:
    if stack_ids is not None:
        return stack_ids
    if first_stack_id is not None and second_stack_id is not None:
        return (first_stack_id, second_stack_id)
    return tuple(initial_battle.unit_stacks)
