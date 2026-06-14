from collections.abc import Callable

from olden.combat.battle import Battle
from olden.combat.coordinates import HexCoord
from olden.combat.movement import find_shortest_paths_to_any
from olden.combat.range import distance_between
from olden.combat.targeting import single_occupied_coordinate

MovementPath = tuple[HexCoord, ...]
PathChooser = Callable[[tuple[MovementPath, ...]], MovementPath]


def choose_engagement_path(
    battle: Battle,
    actor_id: str,
    opponent_id: str,
    path_chooser: PathChooser,
) -> MovementPath | None:
    paths = shortest_engagement_paths(battle, actor_id, opponent_id)
    if not paths:
        return None
    chosen_path = path_chooser(paths)
    if chosen_path not in paths:
        msg = "Path chooser must return one of the available engagement paths"
        raise ValueError(msg)
    return chosen_path


def choose_long_reach_engagement_path(
    battle: Battle,
    actor_id: str,
    opponent_id: str,
    path_chooser: PathChooser,
) -> MovementPath | None:
    paths = shortest_long_reach_engagement_paths(battle, actor_id, opponent_id)
    if not paths:
        return None
    chosen_path = path_chooser(paths)
    if chosen_path not in paths:
        msg = "Path chooser must return one of the available long-reach engagement paths"
        raise ValueError(msg)
    return chosen_path


def shortest_engagement_paths(battle: Battle, actor_id: str, opponent_id: str) -> tuple[MovementPath, ...]:
    paths = reachable_engagement_paths(battle, actor_id, opponent_id)
    if not paths:
        return ()
    shortest_length = min(len(path) for path in paths)
    return tuple(path for path in paths if len(path) == shortest_length)


def shortest_long_reach_engagement_paths(battle: Battle, actor_id: str, opponent_id: str) -> tuple[MovementPath, ...]:
    paths = reachable_long_reach_engagement_paths(battle, actor_id, opponent_id)
    if not paths:
        return ()
    shortest_length = min(len(path) for path in paths)
    return tuple(path for path in paths if len(path) == shortest_length)


def reachable_engagement_paths(battle: Battle, actor_id: str, opponent_id: str) -> tuple[MovementPath, ...]:
    actor_coord = single_occupied_coordinate(battle, actor_id)
    opponent_coord = single_occupied_coordinate(battle, opponent_id)
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


def reachable_long_reach_engagement_paths(battle: Battle, actor_id: str, opponent_id: str) -> tuple[MovementPath, ...]:
    actor_coord = single_occupied_coordinate(battle, actor_id)
    opponent_coord = single_occupied_coordinate(battle, opponent_id)
    candidates = tuple(
        candidate
        for candidate in battle.battlefield.coordinates()
        if distance_between(battle.battlefield, candidate, opponent_coord) == 2
        and battle.occupancy.can_place_coordinate(candidate, moving_unit_id=actor_id)
    )
    return find_shortest_paths_to_any(
        battlefield=battle.battlefield,
        occupancy=battle.occupancy,
        start=actor_coord,
        destinations=candidates,
        moving_unit_id=actor_id,
    )


def destination_for_speed(path: MovementPath, speed: int) -> HexCoord:
    if speed < 0:
        msg = "Movement speed cannot be negative"
        raise ValueError(msg)
    return path[min(speed, len(path) - 1)]


def choose_stay_out_of_melee_reach_path(
    battle: Battle,
    actor_id: str,
    opponent_id: str,
    path_chooser: PathChooser,
) -> MovementPath | None:
    longest_candidates = stay_out_of_melee_reach_paths(battle, actor_id, opponent_id)
    if not longest_candidates:
        return None
    chosen_path = path_chooser(longest_candidates)
    if chosen_path not in longest_candidates:
        msg = "Path chooser must return one of the available stay-out-of-melee-reach paths"
        raise ValueError(msg)
    return chosen_path


def has_stay_out_of_melee_reach_path(battle: Battle, actor_id: str, opponent_id: str) -> bool:
    return bool(stay_out_of_melee_reach_paths(battle, actor_id, opponent_id))


def has_long_reach_engagement_path(battle: Battle, actor_id: str, opponent_id: str) -> bool:
    return bool(shortest_long_reach_engagement_paths(battle, actor_id, opponent_id))


def stay_out_of_melee_reach_paths(battle: Battle, actor_id: str, opponent_id: str) -> tuple[MovementPath, ...]:
    paths = shortest_engagement_paths(battle, actor_id, opponent_id)
    if not paths:
        return ()
    actor_speed = battle.stack(actor_id).definition.speed
    opponent_speed = battle.stack(opponent_id).definition.speed
    opponent_coord = single_occupied_coordinate(battle, opponent_id)
    candidates = tuple(
        path[: index + 1]
        for path in paths
        for index in range(min(actor_speed, len(path) - 1), 0, -1)
        if _is_out_of_melee_reach(battle, path[index], opponent_coord, opponent_speed)
    )
    if not candidates:
        return ()
    longest_length = max(len(path) for path in candidates)
    return tuple(path for path in candidates if len(path) == longest_length)


def are_adjacent(battle: Battle, first_stack_id: str, second_stack_id: str) -> bool:
    first_coord = single_occupied_coordinate(battle, first_stack_id)
    second_coord = single_occupied_coordinate(battle, second_stack_id)
    return second_coord in battle.battlefield.neighbors(first_coord)


def _is_out_of_melee_reach(
    battle: Battle,
    destination: HexCoord,
    opponent_coord: HexCoord,
    opponent_speed: int,
) -> bool:
    return distance_between(battle.battlefield, destination, opponent_coord) > opponent_speed + 1
