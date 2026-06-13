import pytest

from olden.combat.army import Army, army_from_battle_side, estimate_army_matchup, summarize_army
from olden.combat.battle import Battle
from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.heroes import Hero, HeroStats
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.units import AttackCategory, DamageRange, UnitCombatStats, UnitDefinition, UnitStack


def test_army_rejects_stacks_from_mixed_sides():
    attacker = _stack("attacker-esquire", CombatSide.ATTACKER)
    defender = _stack("defender-esquire", CombatSide.DEFENDER)

    with pytest.raises(ValueError, match="side"):
        Army(side=CombatSide.ATTACKER, stacks=(attacker, defender))


def test_army_accepts_optional_hero():
    hero = Hero(
        id="meareas",
        name="Meareas",
        level=3,
        experience=1200,
        stats=HeroStats(attack=2, defense=1, spell_power=0, knowledge=1),
    )

    army = Army(side=CombatSide.ATTACKER, stacks=(_stack("attacker-esquire", CombatSide.ATTACKER),), hero=hero)

    assert army.hero == hero


def test_hero_rejects_invalid_level_and_stats():
    with pytest.raises(ValueError, match="level"):
        Hero(id="meareas", name="Meareas", level=0)

    with pytest.raises(ValueError, match="attack"):
        HeroStats(attack=-1)


def test_army_from_battle_side_includes_only_living_stacks_for_side():
    attacker_front = _stack("attacker-front", CombatSide.ATTACKER)
    attacker_back = _stack("attacker-back", CombatSide.ATTACKER)
    defender = _stack("defender", CombatSide.DEFENDER)
    battlefield = Battlefield.default()
    occupancy = Occupancy(blocked_coordinates=battlefield.blocked_coordinates)
    occupancy.place(attacker_front.id, HexCoord(0, 0))
    occupancy.place(attacker_back.id, HexCoord(0, 1))
    occupancy.place(defender.id, HexCoord(11, 0))
    battle = Battle(
        battlefield=battlefield,
        occupancy=occupancy,
        unit_stacks={stack.id: stack for stack in (attacker_front, defender, attacker_back)},
    )

    army = army_from_battle_side(battle, CombatSide.ATTACKER)

    assert army.side is CombatSide.ATTACKER
    assert army.stacks == (attacker_front, attacker_back)
    assert army.hero is None


def test_summarize_army_keeps_hero_stack_details_and_totals_health_and_base_damage():
    hero = Hero(
        id="meareas",
        name="Meareas",
        level=3,
        experience=1200,
        stats=HeroStats(attack=9, defense=9, spell_power=2, knowledge=3),
    )
    esquires = _stack(
        "attacker-esquires",
        CombatSide.ATTACKER,
        count=10,
        health=12,
        damage=DamageRange(minimum=2, maximum=4),
        wound_damage=5,
    )
    guards = _stack(
        "attacker-guards",
        CombatSide.ATTACKER,
        count=3,
        unit_id="guard",
        unit_name="Guard",
        health=20,
        damage=DamageRange(minimum=5, maximum=6),
    )

    summary = summarize_army(Army(side=CombatSide.ATTACKER, stacks=(esquires, guards), hero=hero))

    assert summary.side is CombatSide.ATTACKER
    assert summary.hero == hero
    assert summary.total_remaining_health == 175
    assert summary.total_average_base_damage_per_turn == 45
    assert [stack.stack_id for stack in summary.stacks] == ["attacker-esquires", "attacker-guards"]
    assert summary.stacks[0].unit_definition_id == "esquire"
    assert summary.stacks[0].unit_name == "Swordsman"
    assert summary.stacks[0].count == 10
    assert summary.stacks[0].remaining_health == 115
    assert summary.stacks[0].average_base_damage == 30
    assert summary.stacks[1].remaining_health == 60
    assert summary.stacks[1].average_base_damage == 15


def test_estimate_army_matchup_exposes_attacker_defender_health_damage_and_favored_side():
    attacker = Army(
        side=CombatSide.ATTACKER,
        stacks=(
            _stack(
                "attacker-esquires",
                CombatSide.ATTACKER,
                count=10,
                health=10,
                damage=DamageRange(minimum=3, maximum=3),
            ),
        ),
    )
    defender = Army(
        side=CombatSide.DEFENDER,
        stacks=(
            _stack(
                "defender-guards",
                CombatSide.DEFENDER,
                count=10,
                health=10,
                damage=DamageRange(minimum=1, maximum=1),
            ),
        ),
    )

    estimate = estimate_army_matchup(attacker=attacker, defender=defender)

    assert estimate.attacker.side is CombatSide.ATTACKER
    assert estimate.defender.side is CombatSide.DEFENDER
    assert estimate.attacker_total_remaining_health == 100
    assert estimate.defender_total_remaining_health == 100
    assert estimate.attacker_average_base_damage_per_turn == 30
    assert estimate.defender_average_base_damage_per_turn == 10
    assert estimate.favored_side is CombatSide.ATTACKER


def test_estimate_army_matchup_has_no_favored_side_for_tied_pressure():
    attacker = Army(
        side=CombatSide.ATTACKER,
        stacks=(_stack("attacker", CombatSide.ATTACKER, count=10, health=10, damage=DamageRange(minimum=2, maximum=2)),),
    )
    defender = Army(
        side=CombatSide.DEFENDER,
        stacks=(_stack("defender", CombatSide.DEFENDER, count=10, health=10, damage=DamageRange(minimum=2, maximum=2)),),
    )

    estimate = estimate_army_matchup(attacker=attacker, defender=defender)

    assert estimate.favored_side is None


def _stack(
    stack_id: str,
    side: CombatSide,
    count: int = 10,
    unit_id: str = "esquire",
    unit_name: str = "Swordsman",
    health: int = 12,
    damage: DamageRange = DamageRange(minimum=2, maximum=3),
    wound_damage: int = 0,
) -> UnitStack:
    return UnitStack(
        id=stack_id,
        definition=UnitDefinition(
            id=unit_id,
            name=unit_name,
            initiative=5,
            speed=4,
            combat=UnitCombatStats(
                health=health,
                attack=4,
                defense=4,
                damage=damage,
                attack_category=AttackCategory.MELEE,
            ),
        ),
        side=side,
        count=count,
        wound_damage=wound_damage,
    )
