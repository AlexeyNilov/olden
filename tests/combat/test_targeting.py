from olden.combat.battle import Battle
from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.targeting import TargetingPolicy, nearest_living_opponent, select_living_opponent
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


def test_threat_removed_targeting_prioritizes_farther_dangerous_units_the_actor_can_kill():
    attacker = _stack("attacker", CombatSide.ATTACKER, count=10, damage=DamageRange(minimum=4, maximum=4))
    defender_near = _stack("defender-near", CombatSide.DEFENDER, count=10, damage=DamageRange(minimum=1, maximum=1))
    defender_dangerous = _stack(
        "defender-dangerous",
        CombatSide.DEFENDER,
        count=1,
        health=10,
        damage=DamageRange(minimum=10, maximum=10),
    )
    battle = _battle(
        (attacker, HexCoord(4, 5)),
        (defender_near, HexCoord(5, 5)),
        (defender_dangerous, HexCoord(8, 5)),
    )

    target_id = select_living_opponent(
        battle,
        "attacker",
        configured_stack_ids=("attacker", "defender-near", "defender-dangerous"),
        policy=TargetingPolicy.THREAT_REMOVED,
    )

    assert target_id == "defender-dangerous"


def test_threat_removed_targeting_uses_nearest_stack_as_score_tie_break():
    attacker = _stack("attacker", CombatSide.ATTACKER, count=10, damage=DamageRange(minimum=4, maximum=4))
    defender_near = _stack("defender-near", CombatSide.DEFENDER, count=1, damage=DamageRange(minimum=10, maximum=10))
    defender_far = _stack("defender-far", CombatSide.DEFENDER, count=1, damage=DamageRange(minimum=10, maximum=10))
    battle = _battle(
        (attacker, HexCoord(4, 5)),
        (defender_near, HexCoord(5, 5)),
        (defender_far, HexCoord(8, 5)),
    )

    target_id = select_living_opponent(
        battle,
        "attacker",
        configured_stack_ids=("attacker", "defender-far", "defender-near"),
        policy=TargetingPolicy.THREAT_REMOVED,
    )

    assert target_id == "defender-near"


def test_threat_removed_targeting_preserves_configured_order_as_final_tie_break():
    attacker = _stack("attacker", CombatSide.ATTACKER, count=10, damage=DamageRange(minimum=4, maximum=4))
    defender_first = _stack("defender-first", CombatSide.DEFENDER, count=1, damage=DamageRange(minimum=10, maximum=10))
    defender_second = _stack("defender-second", CombatSide.DEFENDER, count=1, damage=DamageRange(minimum=10, maximum=10))
    battle = _battle(
        (attacker, HexCoord(4, 5)),
        (defender_first, HexCoord(5, 5)),
        (defender_second, HexCoord(4, 4)),
    )

    target_id = select_living_opponent(
        battle,
        "attacker",
        configured_stack_ids=("attacker", "defender-first", "defender-second"),
        policy=TargetingPolicy.THREAT_REMOVED,
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


def _stack(
    stack_id: str,
    side: CombatSide,
    count: int = 10,
    health: int = 12,
    attack: int = 4,
    defense: int = 4,
    damage: DamageRange = DamageRange(minimum=2, maximum=3),
) -> UnitStack:
    return UnitStack(
        id=stack_id,
        definition=UnitDefinition(
            id=stack_id,
            name=stack_id,
            initiative=5,
            speed=4,
            combat=UnitCombatStats(
                health=health,
                attack=attack,
                defense=defense,
                damage=damage,
                attack_category=AttackCategory.MELEE,
            ),
        ),
        side=side,
        count=count,
    )
