import pytest

from olden.battlefield_view.layout import BattlefieldLayout
from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord


def test_layout_maps_every_valid_battlefield_coordinate_once():
    battlefield = Battlefield.default()
    layout = BattlefieldLayout(hex_radius=10)

    positions = layout.positions_for(battlefield)

    assert len(positions) == 137
    assert {position.coord for position in positions} == set(battlefield.coordinates())


def test_layout_shifts_odd_rows_left_by_half_a_horizontal_step():
    layout = BattlefieldLayout(hex_radius=10)

    even_position = layout.position_for(HexCoord(0, 0))
    odd_position = layout.position_for(HexCoord(0, 1))

    assert odd_position.center_x == pytest.approx(even_position.center_x - layout.horizontal_step / 2)
    assert odd_position.center_y > even_position.center_y


def test_layout_builds_six_polygon_points_for_each_hex():
    layout = BattlefieldLayout(hex_radius=10)

    position = layout.position_for(HexCoord(4, 3))

    assert len(position.points) == 6
