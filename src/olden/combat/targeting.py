from dataclasses import replace
from enum import Enum

from olden.combat.attack import DamageContext, apply_damage_to_stack, calculate_attack_damage
from olden.combat.battle import Battle
from olden.combat.coordinates import HexCoord
from olden.combat.range import distance_between
from olden.combat.units import DamageRange, UnitStack


class TargetingPolicy(Enum):
    NEAREST_OPPONENT = "nearest_opponent"
    THREAT_REMOVED = "threat_removed"


def select_living_opponent(
    battle: Battle,
    actor_id: str,
    configured_stack_ids: tuple[str, ...],
    policy: TargetingPolicy = TargetingPolicy.THREAT_REMOVED,
) -> str | None:
    if policy is TargetingPolicy.NEAREST_OPPONENT:
        return nearest_living_opponent(battle, actor_id, configured_stack_ids)
    if policy is TargetingPolicy.THREAT_REMOVED:
        return highest_threat_removed_opponent(battle, actor_id, configured_stack_ids)
    msg = f"Unsupported targeting policy: {policy}"
    raise ValueError(msg)


def nearest_living_opponent(battle: Battle, actor_id: str, configured_stack_ids: tuple[str, ...]) -> str | None:
    actor_coord = single_occupied_coordinate(battle, actor_id)
    candidates = living_opponents(battle, actor_id, configured_stack_ids)
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda stack_id: distance_between(
            battle.battlefield,
            actor_coord,
            single_occupied_coordinate(battle, stack_id),
        ),
    )


def highest_threat_removed_opponent(battle: Battle, actor_id: str, configured_stack_ids: tuple[str, ...]) -> str | None:
    actor = battle.stack(actor_id)
    actor_coord = single_occupied_coordinate(battle, actor_id)
    candidates = living_opponents(battle, actor_id, configured_stack_ids)
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda stack_id: (
            threat_removed_by_average_attack(actor, battle.stack(stack_id)),
            -distance_between(
                battle.battlefield,
                actor_coord,
                single_occupied_coordinate(battle, stack_id),
            ),
            -configured_stack_ids.index(stack_id),
        ),
    )


def threat_removed_by_average_attack(actor: UnitStack, target: UnitStack) -> int:
    selected_damage = average_damage(actor.definition.combat.damage)
    calculated_damage = calculate_attack_damage(DamageContext(attacker=actor, defender=target, selected_damage=selected_damage))
    damage_application = apply_damage_to_stack(target, calculated_damage.final_damage)
    return damage_application.creatures_killed * average_per_creature_damage_against(target, actor)


def average_per_creature_damage_against(attacker: UnitStack, defender: UnitStack) -> int:
    selected_damage = average_damage(attacker.definition.combat.damage)
    one_creature_attacker = replace(attacker, count=1)
    calculated_damage = calculate_attack_damage(
        DamageContext(attacker=one_creature_attacker, defender=defender, selected_damage=selected_damage)
    )
    return calculated_damage.final_damage


def average_damage(damage: DamageRange) -> int:
    return (damage.minimum + damage.maximum) // 2


def living_opponents(battle: Battle, actor_id: str, configured_stack_ids: tuple[str, ...]) -> tuple[str, ...]:
    actor = battle.stack(actor_id)
    return tuple(
        stack_id
        for stack_id in configured_stack_ids
        if stack_id in battle.unit_stacks and battle.stack(stack_id).side is not actor.side
    )


def one_side_defeated(battle: Battle) -> bool:
    living_sides = {stack.side for stack in battle.unit_stacks.values()}
    return len(living_sides) < 2


def is_defeated(battle: Battle, stack_id: str) -> bool:
    return stack_id not in battle.unit_stacks


def single_occupied_coordinate(battle: Battle, stack_id: str) -> HexCoord:
    coord = battle.occupancy.coordinate_for(stack_id)
    if coord is None:
        msg = f"Expected one occupied coordinate for unit stack: {stack_id}"
        raise ValueError(msg)
    return coord
