import pytest

from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.deployment import DeploymentSide
from olden.combat.obstacles import Obstacle


def test_default_battlefield_exposes_expected_row_lengths():
    battlefield = Battlefield.default()

    assert battlefield.row_lengths == (12, 13, 12, 13, 12, 13, 12, 13, 12, 13, 12)


def test_default_battlefield_contains_exactly_137_valid_coordinates():
    battlefield = Battlefield.default()

    assert len(tuple(battlefield.coordinates())) == 137


def test_battlefield_accepts_valid_edge_and_corner_coordinates():
    battlefield = Battlefield.default()

    assert battlefield.contains(HexCoord(0, 0))
    assert battlefield.contains(HexCoord(11, 0))
    assert battlefield.contains(HexCoord(12, 1))
    assert battlefield.contains(HexCoord(0, 10))
    assert battlefield.contains(HexCoord(11, 10))


@pytest.mark.parametrize(
    "coord",
    [
        HexCoord(-1, 0),
        HexCoord(0, -1),
        HexCoord(12, 0),
        HexCoord(13, 1),
        HexCoord(0, 11),
    ],
)
def test_battlefield_rejects_coordinates_outside_each_row_length(coord):
    battlefield = Battlefield.default()

    with pytest.raises(ValueError, match="Invalid battlefield coordinate"):
        battlefield.require_valid(coord)


def test_battlefield_neighbors_return_only_in_bounds_coordinates_for_center_edge_and_corner_positions():
    battlefield = Battlefield.default()

    assert battlefield.neighbors(HexCoord(5, 5)) == (
        HexCoord(4, 5),
        HexCoord(6, 5),
        HexCoord(4, 4),
        HexCoord(5, 4),
        HexCoord(4, 6),
        HexCoord(5, 6),
    )
    assert battlefield.neighbors(HexCoord(0, 0)) == (
        HexCoord(1, 0),
        HexCoord(0, 1),
        HexCoord(1, 1),
    )
    assert battlefield.neighbors(HexCoord(11, 10)) == (
        HexCoord(10, 10),
        HexCoord(11, 9),
        HexCoord(12, 9),
    )


def test_battlefield_neighbors_follow_odd_row_offset_parity():
    battlefield = Battlefield.default()

    assert battlefield.neighbors(HexCoord(5, 4)) == (
        HexCoord(4, 4),
        HexCoord(6, 4),
        HexCoord(5, 3),
        HexCoord(6, 3),
        HexCoord(5, 5),
        HexCoord(6, 5),
    )


def test_battlefield_hex_exposes_deployment_zone_without_affecting_coordinate_validity():
    battlefield = Battlefield.default()

    left_hex = battlefield.hex_at(HexCoord(0, 4))
    center_hex = battlefield.hex_at(HexCoord(5, 4))
    right_hex = battlefield.hex_at(HexCoord(11, 4))

    assert left_hex.deployment_side is DeploymentSide.PLAYER
    assert center_hex.deployment_side is None
    assert right_hex.deployment_side is DeploymentSide.ENEMY


def test_obstacle_blocks_all_coordinates_it_covers():
    obstacle = Obstacle(name="rocks", coordinates=frozenset({HexCoord(2, 2), HexCoord(3, 2)}))
    battlefield = Battlefield.default(obstacles=(obstacle,))

    assert battlefield.is_blocked(HexCoord(2, 2))
    assert battlefield.is_blocked(HexCoord(3, 2))
    assert not battlefield.is_blocked(HexCoord(4, 2))
