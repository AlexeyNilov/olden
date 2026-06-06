import pytest

from olden.combat.coordinates import HexCoord
from olden.combat.obstacles import Obstacle
from olden.combat.occupancy import Occupancy
from olden.combat.units import UnitFootprint


def test_occupancy_rejects_placing_two_units_on_the_same_coordinate():
    occupancy = Occupancy()
    coord = HexCoord(4, 4)

    occupancy.place("griffin", coord)

    with pytest.raises(ValueError, match="already occupied"):
        occupancy.place("golem", coord)


def test_occupancy_rejects_coordinates_blocked_by_obstacles():
    obstacle = Obstacle(name="tree", coordinates=frozenset({HexCoord(2, 3), HexCoord(3, 3)}))
    occupancy = Occupancy(blocked_coordinates=obstacle.coordinates)

    with pytest.raises(ValueError, match="blocked"):
        occupancy.place("griffin", HexCoord(2, 3))

    with pytest.raises(ValueError, match="blocked"):
        occupancy.place("golem", HexCoord(3, 3))


def test_occupancy_reserves_every_coordinate_in_a_unit_footprint():
    occupancy = Occupancy()
    footprint = UnitFootprint(offsets=frozenset({HexCoord(0, 0), HexCoord(1, 0)}))

    occupancy.place_footprint("cavalry", footprint.coordinates_anchored_at(HexCoord(4, 4)))

    assert occupancy.unit_at(HexCoord(4, 4)) == "cavalry"
    assert occupancy.unit_at(HexCoord(5, 4)) == "cavalry"


def test_occupancy_rejects_unit_footprint_when_secondary_coordinate_is_blocked():
    occupancy = Occupancy(blocked_coordinates=frozenset({HexCoord(5, 4)}))
    footprint = UnitFootprint(offsets=frozenset({HexCoord(0, 0), HexCoord(1, 0)}))

    with pytest.raises(ValueError, match="blocked"):
        occupancy.place_footprint("cavalry", footprint.coordinates_anchored_at(HexCoord(4, 4)))

    assert occupancy.unit_at(HexCoord(4, 4)) is None
    assert occupancy.unit_at(HexCoord(5, 4)) is None


def test_occupancy_rejects_unit_footprint_when_secondary_coordinate_is_occupied():
    occupancy = Occupancy()
    footprint = UnitFootprint(offsets=frozenset({HexCoord(0, 0), HexCoord(1, 0)}))

    occupancy.place("swordsman", HexCoord(5, 4))

    with pytest.raises(ValueError, match="already occupied"):
        occupancy.place_footprint("cavalry", footprint.coordinates_anchored_at(HexCoord(4, 4)))

    assert occupancy.unit_at(HexCoord(4, 4)) is None
    assert occupancy.unit_at(HexCoord(5, 4)) == "swordsman"
