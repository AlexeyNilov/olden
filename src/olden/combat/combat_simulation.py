import random
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from olden.combat.attack import DamageChooser
from olden.combat.battle import Battle
from olden.combat.combat_log import CombatLog, TurnMarker
from olden.combat.coordinates import HexCoord
from olden.combat.movement import UnreachablePathError, find_path
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
    first_stack_id: str,
    second_stack_id: str,
    path_chooser: PathChooser = random.choice,
    damage_chooser: DamageChooser | None = None,
    max_turns: int = 50,
) -> CombatSimulationResult:
    if max_turns < 1:
        msg = "Maximum simulated turns must be positive"
        raise ValueError(msg)

    battle = initial_battle.copy()
    combat_log = CombatLog()
    combat_log.record_battle_started()
    turn_order = (first_stack_id, second_stack_id)
    resolved_damage_chooser = damage_chooser or random_damage

    for turn_index in range(1, max_turns + 1):
        if _is_defeated(battle, first_stack_id) or _is_defeated(battle, second_stack_id):
            return _result(battle, combat_log, CombatSimulationStopReason.STACK_DEFEATED, turn_index - 1)

        actor_id = turn_order[(turn_index - 1) % 2]
        opponent_id = turn_order[turn_index % 2]
        turn = _turn_marker(turn_index)
        if _are_adjacent(battle, actor_id, opponent_id):
            attack = battle.attack_stack(actor_id, opponent_id, resolved_damage_chooser)
            combat_log.record_unit_attacked(turn, attack)
            if _is_defeated(battle, first_stack_id) or _is_defeated(battle, second_stack_id):
                return _result(battle, combat_log, CombatSimulationStopReason.STACK_DEFEATED, turn_index)
            continue

        path = _choose_engagement_path(battle, actor_id, opponent_id, path_chooser)
        if path is None:
            return _result(battle, combat_log, CombatSimulationStopReason.NO_REACHABLE_ENGAGEMENT, turn_index - 1)

        destination = _destination_for_speed(path, battle.stack(actor_id).definition.speed)
        movement = battle.move_stack(actor_id, destination)
        combat_log.record_unit_moved(turn, movement)

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
    paths: list[MovementPath] = []
    for candidate in battle.battlefield.neighbors(opponent_coord):
        if not battle.occupancy.can_place(frozenset({candidate}), moving_unit_id=actor_id):
            continue
        try:
            paths.append(
                find_path(
                    battlefield=battle.battlefield,
                    occupancy=battle.occupancy,
                    start=actor_coord,
                    destination=candidate,
                    moving_unit_id=actor_id,
                )
            )
        except UnreachablePathError:
            continue
    return tuple(paths)


def _destination_for_speed(path: MovementPath, speed: int) -> HexCoord:
    if speed < 0:
        msg = "Movement speed cannot be negative"
        raise ValueError(msg)
    return path[min(speed, len(path) - 1)]


def _turn_marker(turn_index: int) -> TurnMarker:
    return TurnMarker(
        round_number=((turn_index - 1) // 2) + 1,
        turn_number=((turn_index - 1) % 2) + 1,
    )


def _are_adjacent(battle: Battle, first_stack_id: str, second_stack_id: str) -> bool:
    first_coord = _single_occupied_coordinate(battle, first_stack_id)
    second_coord = _single_occupied_coordinate(battle, second_stack_id)
    return second_coord in battle.battlefield.neighbors(first_coord)


def _single_occupied_coordinate(battle: Battle, stack_id: str) -> HexCoord:
    coordinates = battle.occupancy.coordinates_for(stack_id)
    if len(coordinates) != 1:
        msg = f"Expected one occupied coordinate for unit stack: {stack_id}"
        raise ValueError(msg)
    return next(iter(coordinates))


def _is_defeated(battle: Battle, stack_id: str) -> bool:
    return stack_id not in battle.unit_stacks
