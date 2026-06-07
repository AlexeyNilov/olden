from olden.combat.battle import Battle
from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.targeting import nearest_living_opponent
from olden.combat.units import AttackCategory, DamageRange, UnitCombatStats, UnitDefinition, UnitStack


def test_nearest_living_opponent_uses_configured_order_as_distance_tie_break():
    attacker = _stack("attacker", CombatSide.ATTACKER)
    defender_first = _stack("defender-first", CombatSide.DEFENDER)
    defender_second = _stack("defender-second", CombatSide.DEFENDER)
    battle = _battle(
        (attacker, HexCoord(4, 5)),
        (defender_first, HexCoord(5, 5)),
        (defender_second, HexCoord(4, 4)),
    )

    target_id = nearest_living_opponent(
        battle,
        "attacker",
        configured_stack_ids=("attacker", "defender-first", "defender-second"),
    )

    assert target_id == "defender-first"


def _battle(*placements: tuple[UnitStack, HexCoord]) -> Battle:
    battlefield = Battlefield.default()
    occupancy = Occupancy(blocked_coordinates=battlefield.blocked_coordinates)
    for stack, coord in placements:
        occupancy.place(stack.id, coord)
    return Battle(
        battlefield=battlefield,
        occupancy=occupancy,
        unit_stacks={stack.id: stack for stack, _coord in placements},
    )


def _stack(stack_id: str, side: CombatSide) -> UnitStack:
    return UnitStack(
        id=stack_id,
        definition=UnitDefinition(
            id=stack_id,
            name=stack_id,
            initiative=5,
            speed=4,
            combat=UnitCombatStats(
                health=12,
                attack=4,
                defense=4,
                damage=DamageRange(minimum=2, maximum=3),
                attack_category=AttackCategory.MELEE,
            ),
        ),
        side=side,
        count=10,
    )
