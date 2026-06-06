import random
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from olden.combat.battle import Battle
from olden.combat.combat_log import CombatLog, TurnMarker
from olden.combat.coordinates import HexCoord
from olden.combat.movement import UnreachablePathError, find_path

MovementPath = tuple[HexCoord, ...]
PathChooser = Callable[[tuple[MovementPath, ...]], MovementPath]


class MovementSimulationStopReason(Enum):
    ENGAGED = "engaged"
    NO_REACHABLE_ENGAGEMENT = "no_reachable_engagement"
    MAX_TURNS_REACHED = "max_turns_reached"


@dataclass(frozen=True, slots=True)
class MovementSimulationResult:
    battle: Battle
    combat_log: CombatLog
    stop_reason: MovementSimulationStopReason
    turns_taken: int


def simulate_movement_until_engaged(
    initial_battle: Battle,
    first_stack_id: str,
    second_stack_id: str,
    path_chooser: PathChooser = random.choice,
    max_turns: int = 50,
) -> MovementSimulationResult:
    if max_turns < 1:
        msg = "Maximum simulated turns must be positive"
        raise ValueError(msg)

    battle = initial_battle.copy()
    combat_log = CombatLog()
    combat_log.record_battle_started()
    turn_order = (first_stack_id, second_stack_id)

    for turn_index in range(1, max_turns + 1):
        actor_id = turn_order[(turn_index - 1) % 2]
        opponent_id = turn_order[turn_index % 2]
        if _are_adjacent(battle, actor_id, opponent_id):
            return MovementSimulationResult(
                battle=battle,
                combat_log=combat_log,
                stop_reason=MovementSimulationStopReason.ENGAGED,
                turns_taken=turn_index - 1,
            )

        path = _choose_engagement_path(battle, actor_id, opponent_id, path_chooser)
        if path is None:
            return MovementSimulationResult(
                battle=battle,
                combat_log=combat_log,
                stop_reason=MovementSimulationStopReason.NO_REACHABLE_ENGAGEMENT,
                turns_taken=turn_index - 1,
            )

        destination = _destination_for_speed(path, battle.stack(actor_id).definition.speed)
        movement = battle.move_stack(actor_id, destination)
        combat_log.record_unit_moved(_turn_marker(turn_index), movement)

        if _are_adjacent(battle, actor_id, opponent_id):
            return MovementSimulationResult(
                battle=battle,
                combat_log=combat_log,
                stop_reason=MovementSimulationStopReason.ENGAGED,
                turns_taken=turn_index,
            )

    return MovementSimulationResult(
        battle=battle,
        combat_log=combat_log,
        stop_reason=MovementSimulationStopReason.MAX_TURNS_REACHED,
        turns_taken=max_turns,
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
