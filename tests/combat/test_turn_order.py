from olden.combat.battle import Battle
from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.turn_order import order_stacks_for_round
from olden.combat.units import AttackCategory, DamageRange, UnitCombatStats, UnitDefinition, UnitStack


def test_turn_order_uses_initiative_then_speed_then_configured_order():
    battle = _battle(
        _stack("slow", initiative=5, speed=2),
        _stack("fast", initiative=5, speed=6),
        _stack("eager", initiative=9, speed=4),
        _stack("stable-first", initiative=5, speed=6),
    )

    order = order_stacks_for_round(
        battle,
        stack_ids=("slow", "fast", "eager", "stable-first"),
    )

    assert order == ("eager", "fast", "stable-first", "slow")


def test_turn_order_excludes_defeated_stack_ids():
    battle = _battle(
        _stack("slow", initiative=5, speed=2),
        _stack("eager", initiative=9, speed=4),
    )

    order = order_stacks_for_round(
        battle,
        stack_ids=("slow", "defeated", "eager"),
    )

    assert order == ("eager", "slow")


def _battle(*stacks: UnitStack) -> Battle:
    battlefield = Battlefield.default()
    occupancy = Occupancy(blocked_coordinates=battlefield.blocked_coordinates)
    for index, stack in enumerate(stacks):
        occupancy.place(stack.id, HexCoord(index, 0))
    return Battle(
        battlefield=battlefield,
        occupancy=occupancy,
        unit_stacks={stack.id: stack for stack in stacks},
    )


def _stack(stack_id: str, initiative: int, speed: int) -> UnitStack:
    return UnitStack(
        id=stack_id,
        definition=UnitDefinition(
            id=stack_id,
            name=stack_id,
            initiative=initiative,
            speed=speed,
            combat=UnitCombatStats(
                health=12,
                attack=4,
                defense=4,
                damage=DamageRange(minimum=2, maximum=3),
                attack_category=AttackCategory.MELEE,
            ),
        ),
        side=CombatSide.ATTACKER,
        count=10,
    )
