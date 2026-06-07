import random
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from olden.combat.action_opportunities import CombatRoundState
from olden.combat.action_selection import CombatAction, CombatActionSelectionError
from olden.combat.attack import DamageChooser
from olden.combat.battle import Battle
from olden.combat.combat_actions import apply_melee_attack_action, apply_movement_action, apply_skip_action, apply_wait_action
from olden.combat.combat_log import CombatLog, TurnMarker
from olden.combat.engagement import MovementPath as MovementPath
from olden.combat.engagement import (
    PathChooser,
    are_adjacent,
    choose_engagement_path,
    choose_stay_out_of_melee_reach_path,
    destination_for_speed,
    has_stay_out_of_melee_reach_path,
)
from olden.combat.sides import CombatSide
from olden.combat.targeting import TargetingPolicy, is_defeated, one_side_defeated, select_living_opponent
from olden.combat.turn_order import order_stacks_for_round, order_stacks_for_wait_phase
from olden.combat.units import DamageRange

ActionChooser = Callable[[tuple[CombatAction, ...]], CombatAction]
DEFAULT_SIMULATION_ACTIONS = (CombatAction.MELEE_ENGAGE,)


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


@dataclass(frozen=True, slots=True)
class _ActionResult:
    consumed_turn: bool
    stop_reason: CombatSimulationStopReason | None = None


def simulate_combat(
    initial_battle: Battle,
    first_stack_id: str | None = None,
    second_stack_id: str | None = None,
    path_chooser: PathChooser = random.choice,
    damage_chooser: DamageChooser | None = None,
    max_turns: int = 50,
    stack_ids: tuple[str, ...] | None = None,
    targeting_policy: TargetingPolicy = TargetingPolicy.THREAT_REMOVED,
    attacker_actions: tuple[CombatAction, ...] = DEFAULT_SIMULATION_ACTIONS,
    defender_actions: tuple[CombatAction, ...] = DEFAULT_SIMULATION_ACTIONS,
    action_chooser: ActionChooser | None = None,
) -> CombatSimulationResult:
    if max_turns < 1:
        msg = "Maximum simulated turns must be positive"
        raise ValueError(msg)
    configured_stack_ids = _configured_stack_ids(initial_battle, first_stack_id, second_stack_id, stack_ids)

    battle = initial_battle.copy()
    combat_log = CombatLog()
    combat_log.record_battle_started()
    resolved_damage_chooser = damage_chooser or random_damage
    resolved_action_chooser = action_chooser or default_action_chooser
    turns_taken = 0
    round_number = 1

    while turns_taken < max_turns:
        if one_side_defeated(battle):
            return _result(battle, combat_log, CombatSimulationStopReason.STACK_DEFEATED, turns_taken)

        round_order = order_stacks_for_round(battle, configured_stack_ids)
        round_state = CombatRoundState(round_number=round_number)
        turn_number = 1
        for actor_id in round_order:
            if turns_taken >= max_turns:
                return _result(battle, combat_log, CombatSimulationStopReason.MAX_TURNS_REACHED, turns_taken)
            if is_defeated(battle, actor_id):
                turn_number += 1
                continue
            if one_side_defeated(battle):
                return _result(battle, combat_log, CombatSimulationStopReason.STACK_DEFEATED, turns_taken)

            turn = round_state.turn_marker(turn_number)
            action_result = _act_with_stack(
                battle=battle,
                combat_log=combat_log,
                round_state=round_state,
                turn=turn,
                actor_id=actor_id,
                configured_stack_ids=configured_stack_ids,
                path_chooser=path_chooser,
                damage_chooser=resolved_damage_chooser,
                targeting_policy=targeting_policy,
                attacker_actions=attacker_actions,
                defender_actions=defender_actions,
                action_chooser=resolved_action_chooser,
            )
            if action_result.stop_reason is not None:
                return _result(battle, combat_log, action_result.stop_reason, turns_taken)
            if action_result.consumed_turn:
                turns_taken += 1
                if one_side_defeated(battle):
                    return _result(battle, combat_log, CombatSimulationStopReason.STACK_DEFEATED, turns_taken)
            turn_number += 1

        wait_order = order_stacks_for_wait_phase(battle, round_state.waited_stacks(), configured_stack_ids)
        for actor_id in wait_order:
            if turns_taken >= max_turns:
                return _result(battle, combat_log, CombatSimulationStopReason.MAX_TURNS_REACHED, turns_taken)
            if is_defeated(battle, actor_id):
                turn_number += 1
                continue
            if one_side_defeated(battle):
                return _result(battle, combat_log, CombatSimulationStopReason.STACK_DEFEATED, turns_taken)

            turn = round_state.turn_marker(turn_number)
            action_result = _act_with_stack(
                battle=battle,
                combat_log=combat_log,
                round_state=round_state,
                turn=turn,
                actor_id=actor_id,
                configured_stack_ids=configured_stack_ids,
                path_chooser=path_chooser,
                damage_chooser=resolved_damage_chooser,
                targeting_policy=targeting_policy,
                attacker_actions=attacker_actions,
                defender_actions=defender_actions,
                action_chooser=resolved_action_chooser,
            )
            if action_result.stop_reason is not None:
                return _result(battle, combat_log, action_result.stop_reason, turns_taken)
            if action_result.consumed_turn:
                turns_taken += 1
                if one_side_defeated(battle):
                    return _result(battle, combat_log, CombatSimulationStopReason.STACK_DEFEATED, turns_taken)
            turn_number += 1
        round_number += 1

    return _result(battle, combat_log, CombatSimulationStopReason.MAX_TURNS_REACHED, max_turns)


def default_action_chooser(actions: tuple[CombatAction, ...]) -> CombatAction:
    for action in (
        CombatAction.MELEE_ENGAGE,
        CombatAction.STAY_OUT_OF_MELEE_REACH,
        CombatAction.SKIP,
        CombatAction.WAIT,
    ):
        if action in actions:
            return action
    msg = "No combat actions are available"
    raise CombatActionSelectionError(msg)


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


def _act_with_stack(
    battle: Battle,
    combat_log: CombatLog,
    round_state: CombatRoundState,
    turn: TurnMarker,
    actor_id: str,
    configured_stack_ids: tuple[str, ...],
    path_chooser: PathChooser,
    damage_chooser: DamageChooser,
    targeting_policy: TargetingPolicy,
    attacker_actions: tuple[CombatAction, ...],
    defender_actions: tuple[CombatAction, ...],
    action_chooser: ActionChooser,
) -> _ActionResult:
    opponent_id = select_living_opponent(battle, actor_id, configured_stack_ids, targeting_policy)
    if opponent_id is None:
        return _ActionResult(consumed_turn=False, stop_reason=CombatSimulationStopReason.STACK_DEFEATED)

    configured_actions = _actions_for_side(battle, actor_id, attacker_actions, defender_actions)
    applicable_actions = _applicable_actions(
        battle=battle,
        actor_id=actor_id,
        opponent_id=opponent_id,
        configured_actions=configured_actions,
        round_state=round_state,
    )
    if not applicable_actions:
        msg = f"No configured combat action is applicable for unit stack: {actor_id}"
        raise CombatActionSelectionError(msg)
    selected_action = action_chooser(applicable_actions)
    if selected_action not in applicable_actions:
        msg = f"Action chooser returned an unavailable combat action for unit stack: {actor_id}"
        raise CombatActionSelectionError(msg)

    if selected_action is CombatAction.WAIT:
        round_state.record_wait(actor_id)
        apply_wait_action(combat_log, turn, actor_id)
        return _ActionResult(consumed_turn=False)
    if selected_action is CombatAction.SKIP:
        apply_skip_action(combat_log, turn, actor_id)
        return _ActionResult(consumed_turn=True)
    if selected_action is CombatAction.STAY_OUT_OF_MELEE_REACH:
        path = choose_stay_out_of_melee_reach_path(battle, actor_id, opponent_id, path_chooser)
        if path is None:
            msg = f"No stay-out-of-melee-reach path is available for unit stack: {actor_id}"
            raise CombatActionSelectionError(msg)
        apply_movement_action(battle, combat_log, turn, actor_id, path[-1])
        return _ActionResult(consumed_turn=True)

    return _apply_melee_engage_action(
        battle=battle,
        combat_log=combat_log,
        round_state=round_state,
        turn=turn,
        actor_id=actor_id,
        opponent_id=opponent_id,
        path_chooser=path_chooser,
        damage_chooser=damage_chooser,
    )


def _actions_for_side(
    battle: Battle,
    actor_id: str,
    attacker_actions: tuple[CombatAction, ...],
    defender_actions: tuple[CombatAction, ...],
) -> tuple[CombatAction, ...]:
    side = battle.stack(actor_id).side
    if side is CombatSide.ATTACKER:
        return attacker_actions
    return defender_actions


def _applicable_actions(
    battle: Battle,
    actor_id: str,
    opponent_id: str,
    configured_actions: tuple[CombatAction, ...],
    round_state: CombatRoundState,
) -> tuple[CombatAction, ...]:
    applicable: list[CombatAction] = []
    for action in configured_actions:
        if action is CombatAction.WAIT and round_state.can_wait(actor_id):
            applicable.append(action)
        elif action is CombatAction.SKIP:
            applicable.append(action)
        elif action is CombatAction.MELEE_ENGAGE:
            applicable.append(action)
        elif action is CombatAction.STAY_OUT_OF_MELEE_REACH and has_stay_out_of_melee_reach_path(battle, actor_id, opponent_id):
            applicable.append(action)
    return tuple(applicable)


def _apply_melee_engage_action(
    battle: Battle,
    combat_log: CombatLog,
    round_state: CombatRoundState,
    turn: TurnMarker,
    actor_id: str,
    opponent_id: str,
    path_chooser: PathChooser,
    damage_chooser: DamageChooser,
) -> _ActionResult:
    if are_adjacent(battle, actor_id, opponent_id):
        apply_melee_attack_action(
            battle,
            combat_log,
            turn,
            actor_id,
            opponent_id,
            damage_chooser,
            round_state,
        )
        return _ActionResult(consumed_turn=True)

    path = choose_engagement_path(battle, actor_id, opponent_id, path_chooser)
    if path is None:
        return _ActionResult(consumed_turn=False, stop_reason=CombatSimulationStopReason.NO_REACHABLE_ENGAGEMENT)

    destination = destination_for_speed(path, battle.stack(actor_id).definition.speed)
    apply_movement_action(battle, combat_log, turn, actor_id, destination)
    if are_adjacent(battle, actor_id, opponent_id):
        apply_melee_attack_action(
            battle,
            combat_log,
            turn,
            actor_id,
            opponent_id,
            damage_chooser,
            round_state,
        )
    return _ActionResult(consumed_turn=True)
