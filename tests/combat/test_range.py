import pytest

from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.range import distance_between, movement_radius


def test_distance_between_same_coordinate_is_zero():
    battlefield = Battlefield.default()

    assert distance_between(battlefield, HexCoord(4, 5), HexCoord(4, 5)) == 0


def test_distance_between_adjacent_coordinates_is_one():
    battlefield = Battlefield.default()

    assert distance_between(battlefield, HexCoord(4, 5), HexCoord(5, 5)) == 1
    assert distance_between(battlefield, HexCoord(4, 5), HexCoord(4, 4)) == 1


def test_distance_is_symmetric_across_staggered_odd_rows():
    battlefield = Battlefield.default()
    start = HexCoord(4, 5)
    end = HexCoord(5, 3)

    assert distance_between(battlefield, start, end) == distance_between(battlefield, end, start)
    assert distance_between(battlefield, start, end) == 2


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (HexCoord(-1, 0), HexCoord(0, 0)),
        (HexCoord(0, 0), HexCoord(12, 0)),
    ],
)
def test_distance_rejects_invalid_start_or_end_coordinates(start, end):
    battlefield = Battlefield.default()

    with pytest.raises(ValueError, match="Invalid battlefield coordinate"):
        distance_between(battlefield, start, end)


def test_movement_radius_with_zero_speed_contains_only_origin():
    battlefield = Battlefield.default()
    origin = HexCoord(4, 5)

    assert movement_radius(battlefield, origin, speed=0) == frozenset({origin})


def test_movement_radius_includes_all_valid_coordinates_within_speed():
    battlefield = Battlefield.default()
    origin = HexCoord(4, 5)

    radius = movement_radius(battlefield, origin, speed=2)

    assert HexCoord(4, 5) in radius
    assert HexCoord(5, 5) in radius
    assert HexCoord(6, 5) in radius
    assert HexCoord(4, 3) in radius
    assert HexCoord(7, 5) not in radius
    assert all(distance_between(battlefield, origin, coord) <= 2 for coord in radius)


def test_movement_radius_trims_coordinates_outside_battlefield_near_edges():
    battlefield = Battlefield.default()

    radius = movement_radius(battlefield, HexCoord(0, 0), speed=1)

    assert radius == frozenset({HexCoord(0, 0), HexCoord(1, 0), HexCoord(0, 1), HexCoord(1, 1)})


def test_movement_radius_rejects_negative_speed():
    battlefield = Battlefield.default()

    with pytest.raises(ValueError, match="speed"):
        movement_radius(battlefield, HexCoord(4, 5), speed=-1)
