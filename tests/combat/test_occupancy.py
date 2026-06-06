import pytest

from olden.combat.coordinates import HexCoord
from olden.combat.obstacles import Obstacle
from olden.combat.occupancy import Occupancy


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
