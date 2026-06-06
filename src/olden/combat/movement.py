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

    frontier: deque[tuple[HexCoord, ...]] = deque([(start,)])
    visited = {start}

    while frontier:
        path = frontier.popleft()
        for neighbor in battlefield.neighbors(path[-1]):
            if neighbor in visited or not occupancy.can_place(frozenset({neighbor}), moving_unit_id):
                continue

            next_path = (*path, neighbor)
            if neighbor == destination:
                return next_path

            visited.add(neighbor)
            frontier.append(next_path)

    msg = f"No movement path from {start} to {destination}"
    raise UnreachablePathError(msg)


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
    if not occupancy.can_place(frozenset({destination}), moving_unit_id):
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
