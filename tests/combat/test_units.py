import pytest

from olden.combat.sides import CombatSide
from olden.combat.units import AttackCategory, DamageRange, UnitCombatStats, UnitDefinition, UnitStack


def test_unit_definition_exposes_identity_name_initiative_speed_and_combat_stats():
    combat = _combat_stats()

    swordsman = UnitDefinition(
        id="esquire",
        name="Swordsman",
        initiative=5,
        speed=4,
        combat=combat,
    )

    assert swordsman.id == "esquire"
    assert swordsman.name == "Swordsman"
    assert swordsman.initiative == 5
    assert swordsman.speed == 4
    assert swordsman.combat is combat


def test_unit_definition_rejects_negative_initiative():
    with pytest.raises(ValueError, match="initiative"):
        UnitDefinition(
            id="esquire",
            name="Swordsman",
            initiative=-1,
            speed=4,
            combat=_combat_stats(),
        )


def test_unit_definition_rejects_negative_speed():
    with pytest.raises(ValueError, match="speed"):
        UnitDefinition(
            id="esquire",
            name="Swordsman",
            initiative=5,
            speed=-1,
            combat=_combat_stats(),
        )


def test_unit_combat_stats_reject_invalid_values():
    with pytest.raises(ValueError, match="health"):
        _combat_stats(health=0)
    with pytest.raises(ValueError, match="attack"):
        _combat_stats(attack=-1)
    with pytest.raises(ValueError, match="defense"):
        _combat_stats(defense=-1)
    with pytest.raises(ValueError, match="damage"):
        _combat_stats(damage=DamageRange(minimum=4, maximum=3))


def test_unit_stack_exposes_side_definition_and_count():
    swordsman = UnitDefinition(
        id="esquire",
        name="Swordsman",
        initiative=5,
        speed=4,
        combat=_combat_stats(),
    )

    stack = UnitStack(
        id="temple-frontline",
        definition=swordsman,
        side=CombatSide.PLAYER,
        count=25,
        wound_damage=3,
    )

    assert stack.id == "temple-frontline"
    assert stack.definition is swordsman
    assert stack.side is CombatSide.PLAYER
    assert stack.count == 25
    assert stack.wound_damage == 3


def test_unit_stack_rejects_non_positive_count():
    swordsman = UnitDefinition(
        id="esquire",
        name="Swordsman",
        initiative=5,
        speed=4,
        combat=_combat_stats(),
    )

    with pytest.raises(ValueError, match="count"):
        UnitStack(
            id="temple-frontline",
            definition=swordsman,
            side=CombatSide.PLAYER,
            count=0,
        )


def test_unit_stack_rejects_wound_damage_outside_current_creature_health():
    swordsman = UnitDefinition(
        id="esquire",
        name="Swordsman",
        initiative=5,
        speed=4,
        combat=_combat_stats(),
    )

    with pytest.raises(ValueError, match="wound"):
        UnitStack(
            id="temple-frontline",
            definition=swordsman,
            side=CombatSide.PLAYER,
            count=25,
            wound_damage=-1,
        )
    with pytest.raises(ValueError, match="wound"):
        UnitStack(
            id="temple-frontline",
            definition=swordsman,
            side=CombatSide.PLAYER,
            count=25,
            wound_damage=swordsman.combat.health,
        )


def _combat_stats(
    health: int = 12,
    attack: int = 4,
    defense: int = 4,
    damage: DamageRange = DamageRange(minimum=2, maximum=3),
) -> UnitCombatStats:
    return UnitCombatStats(
        health=health,
        attack=attack,
        defense=defense,
        damage=damage,
        attack_category=AttackCategory.MELEE,
    )
