import pytest

from olden.combat.coordinates import HexCoord
from olden.combat.sides import CombatSide
from olden.combat.units import UnitDefinition, UnitFootprint, UnitStack


def test_unit_definition_exposes_identity_name_speed_and_footprint():
    footprint = UnitFootprint.single_hex()

    swordsman = UnitDefinition(
        id="esquire",
        name="Swordsman",
        speed=4,
        footprint=footprint,
    )

    assert swordsman.id == "esquire"
    assert swordsman.name == "Swordsman"
    assert swordsman.speed == 4
    assert swordsman.footprint is footprint


def test_unit_definition_rejects_negative_speed():
    with pytest.raises(ValueError, match="speed"):
        UnitDefinition(
            id="esquire",
            name="Swordsman",
            speed=-1,
            footprint=UnitFootprint.single_hex(),
        )


def test_unit_stack_exposes_side_definition_and_count():
    swordsman = UnitDefinition(
        id="esquire",
        name="Swordsman",
        speed=4,
        footprint=UnitFootprint.single_hex(),
    )

    stack = UnitStack(
        id="temple-frontline",
        definition=swordsman,
        side=CombatSide.PLAYER,
        count=25,
    )

    assert stack.id == "temple-frontline"
    assert stack.definition is swordsman
    assert stack.side is CombatSide.PLAYER
    assert stack.count == 25


def test_unit_stack_rejects_non_positive_count():
    swordsman = UnitDefinition(
        id="esquire",
        name="Swordsman",
        speed=4,
        footprint=UnitFootprint.single_hex(),
    )

    with pytest.raises(ValueError, match="count"):
        UnitStack(
            id="temple-frontline",
            definition=swordsman,
            side=CombatSide.PLAYER,
            count=0,
        )


def test_single_hex_unit_footprint_occupies_anchor_coordinate():
    footprint = UnitFootprint.single_hex()

    assert footprint.coordinates_anchored_at(HexCoord(4, 5)) == frozenset({HexCoord(4, 5)})


def test_multi_hex_unit_footprint_derives_coordinates_from_anchor_and_offsets():
    footprint = UnitFootprint(offsets=frozenset({HexCoord(0, 0), HexCoord(1, 0)}))

    assert footprint.coordinates_anchored_at(HexCoord(4, 5)) == frozenset({HexCoord(4, 5), HexCoord(5, 5)})


def test_unit_footprint_rejects_offsets_that_omit_anchor():
    with pytest.raises(ValueError, match="anchor"):
        UnitFootprint(offsets=frozenset({HexCoord(1, 0)}))
