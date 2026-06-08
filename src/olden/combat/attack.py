from collections.abc import Callable
from dataclasses import dataclass, replace

from olden.combat.battle import Battle
from olden.combat.coordinates import HexCoord
from olden.combat.units import AttackCategory, DamageRange, UnitStack

DamageChooser = Callable[[DamageRange], int]


class MeleeAttackError(ValueError):
    pass


class RangedAttackError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class DamageContext:
    attacker: UnitStack
    defender: UnitStack
    selected_damage: int
    damage_multiplier_percent: int = 100


@dataclass(frozen=True, slots=True)
class CalculatedDamage:
    selected_damage: int
    final_damage: int


@dataclass(frozen=True, slots=True)
class DamageApplicationResult:
    updated_stack: UnitStack | None
    creatures_killed: int
    defender_count_before: int
    defender_count_after: int
    defender_wound_damage_after: int
    defender_defeated: bool


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


@dataclass(frozen=True, slots=True)
class RangedAttackResult:
    primary_damage: AttackDamageResult
    counterattack: AttackDamageResult | None = None


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


def resolve_ranged_attack(
    battle: Battle,
    attacker_id: str,
    defender_id: str,
    damage_chooser: DamageChooser,
) -> RangedAttackResult:
    attacker = battle.stack(attacker_id)
    defender = battle.stack(defender_id)
    _validate_ranged_attack(battle, attacker, defender)

    distance = _distance_between_stacks(battle, attacker.id, defender.id)
    primary_damage = _resolve_attack_damage(
        battle,
        attacker_id,
        defender_id,
        damage_chooser,
        damage_multiplier_percent=range_damage_multiplier_percent(distance),
    )
    return RangedAttackResult(primary_damage=primary_damage)


def can_resolve_ranged_attack(battle: Battle, attacker_id: str, defender_id: str) -> bool:
    try:
        _validate_ranged_attack(battle, battle.stack(attacker_id), battle.stack(defender_id))
    except RangedAttackError:
        return False
    return True


def range_damage_multiplier_percent(distance: int) -> int:
    if distance < 0:
        msg = "Ranged attack distance cannot be negative"
        raise ValueError(msg)
    penalty = min(max(distance - 3, 0) * 10, 50)
    return 100 - penalty


def _validate_melee_attack(battle: Battle, attacker: UnitStack, defender: UnitStack) -> None:
    if attacker.side == defender.side:
        msg = "Melee attack requires opposing unit stacks"
        raise MeleeAttackError(msg)
    if attacker.definition.combat.attack_category not in {AttackCategory.MELEE, AttackCategory.RANGED}:
        msg = "Melee attack requires a melee-capable attacker"
        raise MeleeAttackError(msg)
    attacker_coord = _single_occupied_coordinate(battle, attacker.id)
    defender_coord = _single_occupied_coordinate(battle, defender.id)
    if defender_coord not in battle.battlefield.neighbors(attacker_coord):
        msg = "Melee attack target must be adjacent"
        raise MeleeAttackError(msg)


def _validate_ranged_attack(battle: Battle, attacker: UnitStack, defender: UnitStack) -> None:
    if attacker.side == defender.side:
        msg = "Ranged attack requires opposing unit stacks"
        raise RangedAttackError(msg)
    if attacker.definition.combat.attack_category is not AttackCategory.RANGED:
        msg = "Ranged attack requires a ranged attacker"
        raise RangedAttackError(msg)
    if _has_adjacent_enemy(battle, attacker):
        msg = "Ranged attack is blocked by an adjacent enemy"
        raise RangedAttackError(msg)


def _resolve_attack_damage(
    battle: Battle,
    attacker_id: str,
    defender_id: str,
    damage_chooser: DamageChooser,
    damage_multiplier_percent: int = 100,
) -> AttackDamageResult:
    attacker = battle.stack(attacker_id)
    defender = battle.stack(defender_id)
    selected_damage = _choose_damage(attacker.definition.combat.damage, damage_chooser)
    calculated_damage = calculate_attack_damage(
        DamageContext(
            attacker=attacker,
            defender=defender,
            selected_damage=selected_damage,
            damage_multiplier_percent=damage_multiplier_percent,
        )
    )
    damage_application = apply_damage_to_stack(defender, calculated_damage.final_damage)
    _apply_damage_to_battle(battle, defender_id, damage_application)

    return AttackDamageResult(
        attacker_id=attacker_id,
        defender_id=defender_id,
        selected_damage=calculated_damage.selected_damage,
        final_damage=calculated_damage.final_damage,
        creatures_killed=damage_application.creatures_killed,
        defender_count_before=damage_application.defender_count_before,
        defender_count_after=damage_application.defender_count_after,
        defender_wound_damage_after=damage_application.defender_wound_damage_after,
        defender_defeated=damage_application.defender_defeated,
    )


def _choose_damage(damage: DamageRange, damage_chooser: DamageChooser) -> int:
    selected_damage = damage_chooser(damage)
    if selected_damage < damage.minimum or selected_damage > damage.maximum:
        msg = "Damage chooser must return a value inside the attacker's damage range"
        raise ValueError(msg)
    return selected_damage


def calculate_attack_damage(context: DamageContext) -> CalculatedDamage:
    if context.damage_multiplier_percent < 0:
        msg = "Damage multiplier percent cannot be negative"
        raise ValueError(msg)
    base_damage = context.attacker.count * context.selected_damage
    modified_damage = (
        base_damage * (20 + context.attacker.definition.combat.attack) // (20 + context.defender.definition.combat.defense)
    )
    final_damage = modified_damage * context.damage_multiplier_percent // 100
    return CalculatedDamage(selected_damage=context.selected_damage, final_damage=max(1, final_damage))


def apply_damage_to_stack(defender: UnitStack, final_damage: int) -> DamageApplicationResult:
    total_damage = defender.wound_damage + final_damage
    health = defender.definition.combat.health
    creatures_killed = min(defender.count, total_damage // health)
    count_after = defender.count - creatures_killed
    if count_after == 0:
        return DamageApplicationResult(
            updated_stack=None,
            creatures_killed=creatures_killed,
            defender_count_before=defender.count,
            defender_count_after=0,
            defender_wound_damage_after=0,
            defender_defeated=True,
        )
    wound_damage_after = total_damage % health
    updated_stack = replace(defender, count=count_after, wound_damage=wound_damage_after)
    return DamageApplicationResult(
        updated_stack=updated_stack,
        creatures_killed=creatures_killed,
        defender_count_before=defender.count,
        defender_count_after=updated_stack.count,
        defender_wound_damage_after=updated_stack.wound_damage,
        defender_defeated=False,
    )


def _apply_damage_to_battle(battle: Battle, defender_id: str, damage_application: DamageApplicationResult) -> None:
    if damage_application.updated_stack is None:
        battle.occupancy.remove(defender_id)
        del battle.unit_stacks[defender_id]
        return
    battle.unit_stacks[defender_id] = damage_application.updated_stack


def _can_counterattack(stack: UnitStack) -> bool:
    return stack.definition.combat.attack_category is AttackCategory.MELEE


def _has_adjacent_enemy(battle: Battle, attacker: UnitStack) -> bool:
    attacker_coord = _single_occupied_coordinate(battle, attacker.id)
    adjacent_coords = battle.battlefield.neighbors(attacker_coord)
    return any(
        stack.side != attacker.side and battle.occupancy.coordinate_for(stack.id) in adjacent_coords
        for stack in battle.unit_stacks.values()
    )


def _distance_between_stacks(battle: Battle, first_stack_id: str, second_stack_id: str) -> int:
    from olden.combat.range import distance_between

    return distance_between(
        battle.battlefield,
        _single_occupied_coordinate(battle, first_stack_id),
        _single_occupied_coordinate(battle, second_stack_id),
    )


def _single_occupied_coordinate(battle: Battle, stack_id: str) -> HexCoord:
    coord = battle.occupancy.coordinate_for(stack_id)
    if coord is None:
        msg = f"Expected one occupied coordinate for unit stack: {stack_id}"
        raise MeleeAttackError(msg)
    return coord
