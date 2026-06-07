import pytest

from olden.combat.attack import MeleeAttackError, resolve_melee_attack
from olden.combat.battle import Battle
from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.units import AttackCategory, DamageRange, UnitCombatStats, UnitDefinition, UnitFootprint, UnitStack


def test_melee_attack_damages_adjacent_enemy_stack_and_records_wound_damage():
    battle = _battle(
        player_stack=_stack("player-esquire", CombatSide.PLAYER, count=10),
        enemy_stack=_stack("enemy-esquire", CombatSide.ENEMY, count=20),
        player_anchor=HexCoord(0, 0),
        enemy_anchor=HexCoord(1, 0),
    )

    result = resolve_melee_attack(battle, "player-esquire", "enemy-esquire", damage_chooser=lambda damage: damage.minimum)

    defender = battle.stack("enemy-esquire")
    assert result.primary_damage.final_damage == 20
    assert result.primary_damage.creatures_killed == 1
    assert defender.count == 19
    assert defender.wound_damage == 8


def test_melee_attack_carries_existing_wound_damage_into_later_attacks():
    battle = _battle(
        player_stack=_stack("player-esquire", CombatSide.PLAYER, count=1),
        enemy_stack=_stack("enemy-esquire", CombatSide.ENEMY, count=2, wound_damage=11),
        player_anchor=HexCoord(0, 0),
        enemy_anchor=HexCoord(1, 0),
    )

    result = resolve_melee_attack(battle, "player-esquire", "enemy-esquire", damage_chooser=lambda damage: damage.minimum)

    defender = battle.stack("enemy-esquire")
    assert result.primary_damage.final_damage == 2
    assert result.primary_damage.creatures_killed == 1
    assert defender.count == 1
    assert defender.wound_damage == 1


def test_melee_attack_removes_defeated_stack_from_battle_state_and_occupancy():
    battle = _battle(
        player_stack=_stack("player-esquire", CombatSide.PLAYER, count=10),
        enemy_stack=_stack("enemy-esquire", CombatSide.ENEMY, count=1),
        player_anchor=HexCoord(0, 0),
        enemy_anchor=HexCoord(1, 0),
    )

    result = resolve_melee_attack(battle, "player-esquire", "enemy-esquire", damage_chooser=lambda damage: damage.minimum)

    assert result.primary_damage.defender_defeated is True
    assert "enemy-esquire" not in battle.unit_stacks
    assert battle.occupancy.unit_at(HexCoord(1, 0)) is None
    assert result.counterattack is None


def test_melee_attack_counterattacks_once_when_defender_survives():
    battle = _battle(
        player_stack=_stack("player-esquire", CombatSide.PLAYER, count=10),
        enemy_stack=_stack("enemy-esquire", CombatSide.ENEMY, count=20),
        player_anchor=HexCoord(0, 0),
        enemy_anchor=HexCoord(1, 0),
    )

    result = resolve_melee_attack(battle, "player-esquire", "enemy-esquire", damage_chooser=lambda damage: damage.minimum)

    attacker = battle.stack("player-esquire")
    assert result.counterattack is not None
    assert result.counterattack.attacker_id == "enemy-esquire"
    assert result.counterattack.defender_id == "player-esquire"
    assert result.counterattack.final_damage == 38
    assert attacker.count == 7
    assert attacker.wound_damage == 2


def test_melee_attack_rejects_non_adjacent_target():
    battle = _battle(
        player_stack=_stack("player-esquire", CombatSide.PLAYER, count=10),
        enemy_stack=_stack("enemy-esquire", CombatSide.ENEMY, count=20),
        player_anchor=HexCoord(0, 0),
        enemy_anchor=HexCoord(3, 0),
    )

    with pytest.raises(MeleeAttackError, match="adjacent"):
        resolve_melee_attack(battle, "player-esquire", "enemy-esquire", damage_chooser=lambda damage: damage.minimum)


def test_melee_attack_rejects_same_side_target():
    battle = _battle(
        player_stack=_stack("player-esquire", CombatSide.PLAYER, count=10),
        enemy_stack=_stack("enemy-esquire", CombatSide.PLAYER, count=20),
        player_anchor=HexCoord(0, 0),
        enemy_anchor=HexCoord(1, 0),
    )

    with pytest.raises(MeleeAttackError, match="opposing"):
        resolve_melee_attack(battle, "player-esquire", "enemy-esquire", damage_chooser=lambda damage: damage.minimum)


def test_melee_attack_rounds_fractional_damage_down_with_minimum_one_damage():
    battle = _battle(
        player_stack=_stack(
            "player-esquire",
            CombatSide.PLAYER,
            count=1,
            stats=UnitCombatStats(
                health=12,
                attack=0,
                defense=4,
                damage=DamageRange(minimum=1, maximum=1),
                attack_category=AttackCategory.MELEE,
            ),
        ),
        enemy_stack=_stack(
            "enemy-esquire",
            CombatSide.ENEMY,
            count=20,
            stats=UnitCombatStats(
                health=12,
                attack=4,
                defense=100,
                damage=DamageRange(minimum=2, maximum=3),
                attack_category=AttackCategory.MELEE,
            ),
        ),
        player_anchor=HexCoord(0, 0),
        enemy_anchor=HexCoord(1, 0),
    )

    result = resolve_melee_attack(battle, "player-esquire", "enemy-esquire", damage_chooser=lambda damage: damage.minimum)

    assert result.primary_damage.final_damage == 1
    assert battle.stack("enemy-esquire").wound_damage == 1


def _battle(player_stack: UnitStack, enemy_stack: UnitStack, player_anchor: HexCoord, enemy_anchor: HexCoord) -> Battle:
    battlefield = Battlefield.default()
    occupancy = Occupancy()
    occupancy.place(player_stack.id, player_anchor)
    occupancy.place(enemy_stack.id, enemy_anchor)
    return Battle(
        battlefield=battlefield,
        occupancy=occupancy,
        unit_stacks={player_stack.id: player_stack, enemy_stack.id: enemy_stack},
    )


def _stack(
    stack_id: str,
    side: CombatSide,
    count: int,
    wound_damage: int = 0,
    stats: UnitCombatStats | None = None,
) -> UnitStack:
    return UnitStack(
        id=stack_id,
        definition=UnitDefinition(
            id="esquire",
            name="Swordsman",
            speed=4,
            footprint=UnitFootprint.single_hex(),
            combat=stats
            or UnitCombatStats(
                health=12,
                attack=4,
                defense=4,
                damage=DamageRange(minimum=2, maximum=3),
                attack_category=AttackCategory.MELEE,
            ),
        ),
        side=side,
        count=count,
        wound_damage=wound_damage,
    )
