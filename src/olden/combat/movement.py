from collections import deque

from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.occupancy import Occupancy


class UnreachablePathError(ValueError):
    pass


def find_path(
    battlefield: Battlefield,
    occupancy: Occupancy,
    start: HexCoord,
    destination: HexCoord,
    moving_unit_id: str,
) -> tuple[HexCoord, ...]:
    battlefield.require_valid(start)
    battlefield.require_valid(destination)
    if start == destination:
        return (start,)

    frontier: deque[HexCoord] = deque([start])
    predecessors: dict[HexCoord, HexCoord | None] = {start: None}

    while frontier:
        current = frontier.popleft()
        for neighbor in battlefield.neighbors(current):
            if neighbor in predecessors or not occupancy.can_place_coordinate(neighbor, moving_unit_id):
                continue

            predecessors[neighbor] = current
            if neighbor == destination:
                return _reconstruct_path(predecessors, destination)

            frontier.append(neighbor)

    msg = f"No movement path from {start} to {destination}"
    raise UnreachablePathError(msg)


def find_shortest_paths_to_any(
    battlefield: Battlefield,
    occupancy: Occupancy,
    start: HexCoord,
    destinations: tuple[HexCoord, ...],
    moving_unit_id: str,
) -> tuple[tuple[HexCoord, ...], ...]:
    battlefield.require_valid(start)
    for destination in destinations:
        battlefield.require_valid(destination)
    if not destinations:
        return ()

    destination_set = frozenset(destinations)
    frontier: deque[HexCoord] = deque([start])
    predecessors: dict[HexCoord, HexCoord | None] = {start: None}
    distances = {start: 0}
    shortest_distance: int | None = 0 if start in destination_set else None

    while frontier:
        current = frontier.popleft()
        current_distance = distances[current]
        if shortest_distance is not None and current_distance >= shortest_distance:
            continue

        for neighbor in battlefield.neighbors(current):
            if neighbor in predecessors or not occupancy.can_place_coordinate(neighbor, moving_unit_id):
                continue

            next_distance = current_distance + 1
            predecessors[neighbor] = current
            distances[neighbor] = next_distance
            if neighbor in destination_set:
                shortest_distance = next_distance if shortest_distance is None else min(shortest_distance, next_distance)
                continue
            if shortest_distance is None or next_distance < shortest_distance:
                frontier.append(neighbor)

    if shortest_distance is None:
        return ()

    return tuple(
        _reconstruct_path(predecessors, destination)
        for destination in destinations
        if distances.get(destination) == shortest_distance
    )


def validate_movement(
    battlefield: Battlefield,
    occupancy: Occupancy,
    start: HexCoord,
    destination: HexCoord,
    speed: int,
    moving_unit_id: str,
) -> tuple[HexCoord, ...]:
    if speed < 0:
        msg = "Movement speed cannot be negative"
        raise ValueError(msg)

    battlefield.require_valid(start)
    battlefield.require_valid(destination)
    if not occupancy.can_place_coordinate(destination, moving_unit_id):
        msg = f"Movement destination is not passable: {destination}"
        raise ValueError(msg)

    path = find_path(
        battlefield=battlefield,
        occupancy=occupancy,
        start=start,
        destination=destination,
        moving_unit_id=moving_unit_id,
    )
    if len(path) - 1 > speed:
        msg = f"Movement path exceeds unit speed: {speed}"
        raise ValueError(msg)
    return path


def _reconstruct_path(predecessors: dict[HexCoord, HexCoord | None], destination: HexCoord) -> tuple[HexCoord, ...]:
    path = [destination]
    current = destination
    while predecessors[current] is not None:
        previous = predecessors[current]
        if previous is None:
            break
        current = previous
        path.append(current)
    path.reverse()
    return tuple(path)
