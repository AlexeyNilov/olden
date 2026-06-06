from olden.battlefield_view.model import build_battlefield_view
from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.obstacles import Obstacle
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.units import UnitDefinition, UnitFootprint, UnitStack


def test_battlefield_view_exposes_deployment_zone_state_for_each_renderable_hex():
    view = build_battlefield_view(Battlefield.default(), Occupancy())

    assert view.hex_at(HexCoord(0, 4)).deployment_side is CombatSide.PLAYER
    assert view.hex_at(HexCoord(5, 4)).deployment_side is None
    assert view.hex_at(HexCoord(11, 4)).deployment_side is CombatSide.ENEMY


def test_battlefield_view_exposes_blocked_state_for_obstacle_coordinates():
    obstacle = Obstacle(name="rocks", coordinates=frozenset({HexCoord(2, 3)}))
    battlefield = Battlefield.default(obstacles=(obstacle,))

    view = build_battlefield_view(battlefield, Occupancy(blocked_coordinates=obstacle.coordinates))

    assert view.hex_at(HexCoord(2, 3)).is_blocked
    assert not view.hex_at(HexCoord(3, 3)).is_blocked


def test_battlefield_view_exposes_occupying_unit_identity_and_optional_stack_metadata():
    swordsman = UnitStack(
        id="unit-1",
        definition=UnitDefinition(id="swordsman", name="Swordsman", speed=4, footprint=UnitFootprint.single_hex()),
        side=CombatSide.PLAYER,
        count=12,
    )
    occupancy = Occupancy()
    occupancy.place(swordsman.id, HexCoord(4, 5))

    view = build_battlefield_view(Battlefield.default(), occupancy, unit_stacks={swordsman.id: swordsman})

    renderable_hex = view.hex_at(HexCoord(4, 5))
    assert renderable_hex.occupant_id == swordsman.id
    assert renderable_hex.unit_stack == swordsman


def test_battlefield_view_does_not_mutate_occupancy():
    occupancy = Occupancy()
    occupancy.place("unit-1", HexCoord(4, 5))

    build_battlefield_view(Battlefield.default(), occupancy)

    assert occupancy.unit_at(HexCoord(4, 5)) == "unit-1"
