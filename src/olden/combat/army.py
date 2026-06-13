from dataclasses import dataclass

from olden.combat.battle import Battle
from olden.combat.heroes import Hero
from olden.combat.sides import CombatSide
from olden.combat.units import UnitStack


@dataclass(frozen=True, slots=True)
class Army:
    side: CombatSide
    stacks: tuple[UnitStack, ...]
    hero: Hero | None = None

    def __post_init__(self) -> None:
        for stack in self.stacks:
            if stack.side is not self.side:
                msg = "Army unit stacks must all belong to the army side"
                raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class ArmyStackSummary:
    stack_id: str
    unit_definition_id: str
    unit_name: str
    count: int
    remaining_health: int
    average_base_damage: int


@dataclass(frozen=True, slots=True)
class ArmySummary:
    side: CombatSide
    stacks: tuple[ArmyStackSummary, ...]
    total_remaining_health: int
    total_average_base_damage_per_turn: int
    hero: Hero | None = None


@dataclass(frozen=True, slots=True)
class ArmyMatchupEstimate:
    attacker: ArmySummary
    defender: ArmySummary
    attacker_total_remaining_health: int
    defender_total_remaining_health: int
    attacker_average_base_damage_per_turn: int
    defender_average_base_damage_per_turn: int
    favored_side: CombatSide | None


def army_from_battle_side(battle: Battle, side: CombatSide) -> Army:
    return Army(side=side, stacks=tuple(stack for stack in battle.unit_stacks.values() if stack.side is side))


def summarize_army(army: Army) -> ArmySummary:
    stack_summaries = tuple(_summarize_stack(stack) for stack in army.stacks)
    return ArmySummary(
        side=army.side,
        stacks=stack_summaries,
        total_remaining_health=sum(stack.remaining_health for stack in stack_summaries),
        total_average_base_damage_per_turn=sum(stack.average_base_damage for stack in stack_summaries),
        hero=army.hero,
    )


def estimate_army_matchup(attacker: Army, defender: Army) -> ArmyMatchupEstimate:
    if attacker.side is not CombatSide.ATTACKER:
        msg = "Attacker army must use the attacker combat side"
        raise ValueError(msg)
    if defender.side is not CombatSide.DEFENDER:
        msg = "Defender army must use the defender combat side"
        raise ValueError(msg)

    attacker_summary = summarize_army(attacker)
    defender_summary = summarize_army(defender)
    return ArmyMatchupEstimate(
        attacker=attacker_summary,
        defender=defender_summary,
        attacker_total_remaining_health=attacker_summary.total_remaining_health,
        defender_total_remaining_health=defender_summary.total_remaining_health,
        attacker_average_base_damage_per_turn=attacker_summary.total_average_base_damage_per_turn,
        defender_average_base_damage_per_turn=defender_summary.total_average_base_damage_per_turn,
        favored_side=_favored_side(attacker_summary, defender_summary),
    )


def _summarize_stack(stack: UnitStack) -> ArmyStackSummary:
    return ArmyStackSummary(
        stack_id=stack.id,
        unit_definition_id=stack.definition.id,
        unit_name=stack.definition.name,
        count=stack.count,
        remaining_health=stack.count * stack.definition.combat.health - stack.wound_damage,
        average_base_damage=stack.count * _average_damage(stack),
    )


def _average_damage(stack: UnitStack) -> int:
    damage = stack.definition.combat.damage
    return (damage.minimum + damage.maximum) // 2


def _favored_side(attacker: ArmySummary, defender: ArmySummary) -> CombatSide | None:
    attacker_turns_to_defeat = _turns_to_defeat(
        health=defender.total_remaining_health,
        damage_per_turn=attacker.total_average_base_damage_per_turn,
    )
    defender_turns_to_defeat = _turns_to_defeat(
        health=attacker.total_remaining_health,
        damage_per_turn=defender.total_average_base_damage_per_turn,
    )
    if attacker_turns_to_defeat == defender_turns_to_defeat:
        return None
    if attacker_turns_to_defeat is None:
        return CombatSide.DEFENDER
    if defender_turns_to_defeat is None:
        return CombatSide.ATTACKER
    if attacker_turns_to_defeat < defender_turns_to_defeat:
        return CombatSide.ATTACKER
    return CombatSide.DEFENDER


def _turns_to_defeat(health: int, damage_per_turn: int) -> int | None:
    if health <= 0:
        return 0
    if damage_per_turn <= 0:
        return None
    return (health + damage_per_turn - 1) // damage_per_turn
