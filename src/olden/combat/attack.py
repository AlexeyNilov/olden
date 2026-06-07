from collections.abc import Callable
from dataclasses import dataclass, replace

from olden.combat.battle import Battle
from olden.combat.coordinates import HexCoord
from olden.combat.units import AttackCategory, DamageRange, UnitStack

DamageChooser = Callable[[DamageRange], int]


class MeleeAttackError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class AttackDamageResult:
    attacker_id: str
    defender_id: str
    selected_damage: int
    final_damage: int
    creatures_killed: int
    defender_count_before: int
    defender_count_after: int
    defender_wound_damage_after: int
    defender_defeated: bool


@dataclass(frozen=True, slots=True)
class MeleeAttackResult:
    primary_damage: AttackDamageResult
    counterattack: AttackDamageResult | None


def resolve_melee_attack(
    battle: Battle,
    attacker_id: str,
    defender_id: str,
    damage_chooser: DamageChooser,
    allow_counterattack: bool = True,
) -> MeleeAttackResult:
    attacker = battle.stack(attacker_id)
    defender = battle.stack(defender_id)
    _validate_melee_attack(battle, attacker, defender)

    primary_damage = _resolve_attack_damage(battle, attacker_id, defender_id, damage_chooser)
    counterattack = None
    if allow_counterattack and not primary_damage.defender_defeated and _can_counterattack(battle.stack(defender_id)):
        counterattack = _resolve_attack_damage(battle, defender_id, attacker_id, damage_chooser)

    return MeleeAttackResult(primary_damage=primary_damage, counterattack=counterattack)


def _validate_melee_attack(battle: Battle, attacker: UnitStack, defender: UnitStack) -> None:
    if attacker.side == defender.side:
        msg = "Melee attack requires opposing unit stacks"
        raise MeleeAttackError(msg)
    if attacker.definition.combat.attack_category is not AttackCategory.MELEE:
        msg = "Melee attack requires a melee attacker"
        raise MeleeAttackError(msg)
    attacker_coord = _single_occupied_coordinate(battle, attacker.id)
    defender_coord = _single_occupied_coordinate(battle, defender.id)
    if defender_coord not in battle.battlefield.neighbors(attacker_coord):
        msg = "Melee attack target must be adjacent"
        raise MeleeAttackError(msg)


def _resolve_attack_damage(
    battle: Battle,
    attacker_id: str,
    defender_id: str,
    damage_chooser: DamageChooser,
) -> AttackDamageResult:
    attacker = battle.stack(attacker_id)
    defender = battle.stack(defender_id)
    selected_damage = _choose_damage(attacker.definition.combat.damage, damage_chooser)
    final_damage = _calculate_final_damage(attacker, defender, selected_damage)
    updated_defender, creatures_killed = _apply_damage(defender, final_damage)
    if updated_defender is None:
        battle.occupancy.remove(defender_id)
        del battle.unit_stacks[defender_id]
        defender_count_after = 0
        defender_wound_damage_after = 0
        defender_defeated = True
    else:
        battle.unit_stacks[defender_id] = updated_defender
        defender_count_after = updated_defender.count
        defender_wound_damage_after = updated_defender.wound_damage
        defender_defeated = False

    return AttackDamageResult(
        attacker_id=attacker_id,
        defender_id=defender_id,
        selected_damage=selected_damage,
        final_damage=final_damage,
        creatures_killed=creatures_killed,
        defender_count_before=defender.count,
        defender_count_after=defender_count_after,
        defender_wound_damage_after=defender_wound_damage_after,
        defender_defeated=defender_defeated,
    )


def _choose_damage(damage: DamageRange, damage_chooser: DamageChooser) -> int:
    selected_damage = damage_chooser(damage)
    if selected_damage < damage.minimum or selected_damage > damage.maximum:
        msg = "Damage chooser must return a value inside the attacker's damage range"
        raise ValueError(msg)
    return selected_damage


def _calculate_final_damage(attacker: UnitStack, defender: UnitStack, selected_damage: int) -> int:
    base_damage = attacker.count * selected_damage
    modified_damage = base_damage * (20 + attacker.definition.combat.attack) // (20 + defender.definition.combat.defense)
    return max(1, modified_damage)


def _apply_damage(defender: UnitStack, damage: int) -> tuple[UnitStack | None, int]:
    total_damage = defender.wound_damage + damage
    health = defender.definition.combat.health
    creatures_killed = min(defender.count, total_damage // health)
    count_after = defender.count - creatures_killed
    if count_after == 0:
        return None, creatures_killed
    wound_damage_after = total_damage % health
    return replace(defender, count=count_after, wound_damage=wound_damage_after), creatures_killed


def _can_counterattack(stack: UnitStack) -> bool:
    return stack.definition.combat.attack_category is AttackCategory.MELEE


def _single_occupied_coordinate(battle: Battle, stack_id: str) -> HexCoord:
    coordinates = battle.occupancy.coordinates_for(stack_id)
    if len(coordinates) != 1:
        msg = f"Expected one occupied coordinate for unit stack: {stack_id}"
        raise MeleeAttackError(msg)
    return next(iter(coordinates))
