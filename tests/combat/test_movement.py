import pytest

from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.movement import UnreachablePathError, find_path, validate_movement
from olden.combat.obstacles import Obstacle
from olden.combat.occupancy import Occupancy


def test_find_path_returns_shortest_path_across_unobstructed_neighbors():
    battlefield = Battlefield.default()
    occupancy = Occupancy()

    path = find_path(
        battlefield=battlefield,
        occupancy=occupancy,
        start=HexCoord(4, 4),
        destination=HexCoord(6, 4),
        moving_unit_id="swordsman",
    )

    assert path == (HexCoord(4, 4), HexCoord(5, 4), HexCoord(6, 4))


def test_find_path_routes_around_obstacle_coordinates():
    obstacle = Obstacle(name="rocks", coordinates=frozenset({HexCoord(5, 4)}))
    battlefield = Battlefield.default(obstacles=(obstacle,))
    occupancy = Occupancy(blocked_coordinates=obstacle.coordinates)

    path = find_path(
        battlefield=battlefield,
        occupancy=occupancy,
        start=HexCoord(4, 4),
        destination=HexCoord(6, 4),
        moving_unit_id="swordsman",
    )

    assert path[0] == HexCoord(4, 4)
    assert path[-1] == HexCoord(6, 4)
    assert HexCoord(5, 4) not in path
    assert len(path) == 4


def test_find_path_routes_around_occupied_coordinates():
    battlefield = Battlefield.default()
    occupancy = Occupancy()
    occupancy.place("golem", HexCoord(5, 4))

    path = find_path(
        battlefield=battlefield,
        occupancy=occupancy,
        start=HexCoord(4, 4),
        destination=HexCoord(6, 4),
        moving_unit_id="swordsman",
    )

    assert path[0] == HexCoord(4, 4)
    assert path[-1] == HexCoord(6, 4)
    assert HexCoord(5, 4) not in path
    assert len(path) == 4


def test_find_path_raises_dedicated_exception_for_unreachable_destinations():
    obstacle = Obstacle(
        name="ring",
        coordinates=frozenset(
            {
                HexCoord(4, 5),
                HexCoord(6, 5),
                HexCoord(4, 4),
                HexCoord(5, 4),
                HexCoord(4, 6),
                HexCoord(5, 6),
            }
        ),
    )
    battlefield = Battlefield.default(obstacles=(obstacle,))
    occupancy = Occupancy(blocked_coordinates=obstacle.coordinates)

    with pytest.raises(UnreachablePathError):
        find_path(
            battlefield=battlefield,
            occupancy=occupancy,
            start=HexCoord(8, 5),
            destination=HexCoord(5, 5),
            moving_unit_id="swordsman",
        )


def test_validate_movement_accepts_destination_with_path_cost_within_speed():
    battlefield = Battlefield.default()
    occupancy = Occupancy()
    occupancy.place("swordsman", HexCoord(4, 4))

    path = validate_movement(
        battlefield=battlefield,
        occupancy=occupancy,
        start=HexCoord(4, 4),
        destination=HexCoord(6, 4),
        speed=2,
        moving_unit_id="swordsman",
    )

    assert path == (HexCoord(4, 4), HexCoord(5, 4), HexCoord(6, 4))
    assert occupancy.unit_at(HexCoord(4, 4)) == "swordsman"
    assert occupancy.unit_at(HexCoord(6, 4)) is None


def test_validate_movement_rejects_destination_beyond_speed():
    battlefield = Battlefield.default()
    occupancy = Occupancy()

    with pytest.raises(ValueError, match="speed"):
        validate_movement(
            battlefield=battlefield,
            occupancy=occupancy,
            start=HexCoord(4, 4),
            destination=HexCoord(7, 4),
            speed=2,
            moving_unit_id="swordsman",
        )


@pytest.mark.parametrize(
    ("start", "destination"),
    [
        (HexCoord(-1, 0), HexCoord(0, 0)),
        (HexCoord(0, 0), HexCoord(12, 0)),
    ],
)
def test_validate_movement_rejects_invalid_start_or_destination_coordinates(start, destination):
    battlefield = Battlefield.default()
    occupancy = Occupancy()

    with pytest.raises(ValueError, match="Invalid battlefield coordinate"):
        validate_movement(
            battlefield=battlefield,
            occupancy=occupancy,
            start=start,
            destination=destination,
            speed=2,
            moving_unit_id="swordsman",
        )


def test_validate_movement_rejects_blocked_destinations():
    obstacle = Obstacle(name="rocks", coordinates=frozenset({HexCoord(5, 4)}))
    battlefield = Battlefield.default(obstacles=(obstacle,))
    occupancy = Occupancy(blocked_coordinates=obstacle.coordinates)

    with pytest.raises(ValueError, match="destination"):
        validate_movement(
            battlefield=battlefield,
            occupancy=occupancy,
            start=HexCoord(4, 4),
            destination=HexCoord(5, 4),
            speed=2,
            moving_unit_id="swordsman",
        )


def test_validate_movement_rejects_destinations_occupied_by_other_units():
    battlefield = Battlefield.default()
    occupancy = Occupancy()
    occupancy.place("golem", HexCoord(5, 4))

    with pytest.raises(ValueError, match="destination"):
        validate_movement(
            battlefield=battlefield,
            occupancy=occupancy,
            start=HexCoord(4, 4),
            destination=HexCoord(5, 4),
            speed=2,
            moving_unit_id="swordsman",
        )
