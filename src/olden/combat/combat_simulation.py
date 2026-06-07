import random
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from olden.combat.attack import DamageChooser
from olden.combat.battle import Battle
from olden.combat.combat_log import CombatLog, TurnMarker
from olden.combat.coordinates import HexCoord
from olden.combat.movement import find_shortest_paths_to_any
from olden.combat.range import distance_between
from olden.combat.turn_order import order_stacks_for_round
from olden.combat.units import DamageRange

MovementPath = tuple[HexCoord, ...]
PathChooser = Callable[[tuple[MovementPath, ...]], MovementPath]


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
        if _one_side_defeated(battle):
            return _result(battle, combat_log, CombatSimulationStopReason.STACK_DEFEATED, turns_taken)

        round_order = order_stacks_for_round(battle, configured_stack_ids)
        counterattacked_stack_ids: set[str] = set()
        for turn_number, actor_id in enumerate(round_order, start=1):
            if turns_taken >= max_turns:
                return _result(battle, combat_log, CombatSimulationStopReason.MAX_TURNS_REACHED, turns_taken)
            if _is_defeated(battle, actor_id):
                continue
            if _one_side_defeated(battle):
                return _result(battle, combat_log, CombatSimulationStopReason.STACK_DEFEATED, turns_taken)

            opponent_id = _nearest_living_enemy(battle, actor_id, configured_stack_ids)
            if opponent_id is None:
                return _result(battle, combat_log, CombatSimulationStopReason.STACK_DEFEATED, turns_taken)

            turn = TurnMarker(round_number=round_number, turn_number=turn_number)
            if _are_adjacent(battle, actor_id, opponent_id):
                _attack_and_record(
                    battle,
                    combat_log,
                    turn,
                    actor_id,
                    opponent_id,
                    resolved_damage_chooser,
                    counterattacked_stack_ids,
                )
                turns_taken += 1
                if _one_side_defeated(battle):
                    return _result(battle, combat_log, CombatSimulationStopReason.STACK_DEFEATED, turns_taken)
                continue

            path = _choose_engagement_path(battle, actor_id, opponent_id, path_chooser)
            if path is None:
                return _result(battle, combat_log, CombatSimulationStopReason.NO_REACHABLE_ENGAGEMENT, turns_taken)

            destination = _destination_for_speed(path, battle.stack(actor_id).definition.speed)
            movement = battle.move_stack(actor_id, destination)
            combat_log.record_unit_moved(turn, movement)
            if _are_adjacent(battle, actor_id, opponent_id):
                _attack_and_record(
                    battle,
                    combat_log,
                    turn,
                    actor_id,
                    opponent_id,
                    resolved_damage_chooser,
                    counterattacked_stack_ids,
                )
            turns_taken += 1
            if _one_side_defeated(battle):
                return _result(battle, combat_log, CombatSimulationStopReason.STACK_DEFEATED, turns_taken)
        round_number += 1

    return _result(battle, combat_log, CombatSimulationStopReason.MAX_TURNS_REACHED, max_turns)


def random_damage(damage: DamageRange) -> int:
    return random.randint(damage.minimum, damage.maximum)


def _attack_and_record(
    battle: Battle,
    combat_log: CombatLog,
    turn: TurnMarker,
    actor_id: str,
    opponent_id: str,
    damage_chooser: DamageChooser,
    counterattacked_stack_ids: set[str],
) -> None:
    attack = battle.attack_stack(
        actor_id,
        opponent_id,
        damage_chooser,
        allow_counterattack=opponent_id not in counterattacked_stack_ids,
    )
    if attack.counterattack is not None:
        counterattacked_stack_ids.add(opponent_id)
    combat_log.record_unit_attacked(turn, attack)


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


def _choose_engagement_path(
    battle: Battle,
    actor_id: str,
    opponent_id: str,
    path_chooser: PathChooser,
) -> MovementPath | None:
    paths = _shortest_engagement_paths(battle, actor_id, opponent_id)
    if not paths:
        return None
    chosen_path = path_chooser(paths)
    if chosen_path not in paths:
        msg = "Path chooser must return one of the available engagement paths"
        raise ValueError(msg)
    return chosen_path


def _shortest_engagement_paths(battle: Battle, actor_id: str, opponent_id: str) -> tuple[MovementPath, ...]:
    paths = _reachable_engagement_paths(battle, actor_id, opponent_id)
    if not paths:
        return ()
    shortest_length = min(len(path) for path in paths)
    return tuple(path for path in paths if len(path) == shortest_length)


def _reachable_engagement_paths(battle: Battle, actor_id: str, opponent_id: str) -> tuple[MovementPath, ...]:
    actor_coord = _single_occupied_coordinate(battle, actor_id)
    opponent_coord = _single_occupied_coordinate(battle, opponent_id)
    candidates = tuple(
        candidate
        for candidate in battle.battlefield.neighbors(opponent_coord)
        if battle.occupancy.can_place_coordinate(candidate, moving_unit_id=actor_id)
    )
    return find_shortest_paths_to_any(
        battlefield=battle.battlefield,
        occupancy=battle.occupancy,
        start=actor_coord,
        destinations=candidates,
        moving_unit_id=actor_id,
    )


def _destination_for_speed(path: MovementPath, speed: int) -> HexCoord:
    if speed < 0:
        msg = "Movement speed cannot be negative"
        raise ValueError(msg)
    return path[min(speed, len(path) - 1)]


def _are_adjacent(battle: Battle, first_stack_id: str, second_stack_id: str) -> bool:
    first_coord = _single_occupied_coordinate(battle, first_stack_id)
    second_coord = _single_occupied_coordinate(battle, second_stack_id)
    return second_coord in battle.battlefield.neighbors(first_coord)


def _single_occupied_coordinate(battle: Battle, stack_id: str) -> HexCoord:
    coord = battle.occupancy.coordinate_for(stack_id)
    if coord is None:
        msg = f"Expected one occupied coordinate for unit stack: {stack_id}"
        raise ValueError(msg)
    return coord


def _is_defeated(battle: Battle, stack_id: str) -> bool:
    return stack_id not in battle.unit_stacks


def _one_side_defeated(battle: Battle) -> bool:
    living_sides = {stack.side for stack in battle.unit_stacks.values()}
    return len(living_sides) < 2


def _nearest_living_enemy(battle: Battle, actor_id: str, configured_stack_ids: tuple[str, ...]) -> str | None:
    actor = battle.stack(actor_id)
    actor_coord = _single_occupied_coordinate(battle, actor_id)
    candidates = tuple(
        stack_id
        for stack_id in configured_stack_ids
        if stack_id in battle.unit_stacks and battle.stack(stack_id).side is not actor.side
    )
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda stack_id: distance_between(
            battle.battlefield,
            actor_coord,
            _single_occupied_coordinate(battle, stack_id),
        ),
    )
