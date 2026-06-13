import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from olden.combat.action_opportunities import CombatRoundState
from olden.combat.army import (
    Army,
    ArmyMatchupEstimate,
    ArmySummary,
    army_from_battle_side,
    estimate_army_matchup,
    summarize_army,
)
from olden.combat.army_setup import load_army_file
from olden.combat.battle import Battle
from olden.combat.battlefield import Battlefield
from olden.combat.combat_actions import apply_melee_attack_action
from olden.combat.combat_log import CombatLog, UnitAttackedEvent
from olden.combat.coordinates import HexCoord
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.targeting import one_side_defeated
from olden.combat.turn_order import order_stacks_for_round
from olden.combat.units import DamageRange
from olden.hero_data.packaged import load_packaged_hero_catalog
from olden.unit_data.packaged import load_packaged_unit_catalog

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ATTACKER_ARMY_PATH = PROJECT_ROOT / "data" / "army" / "temple.yaml"
DEFAULT_DEFENDER_ARMY_PATH = PROJECT_ROOT / "data" / "object" / "altar_of_meareas.yaml"
ATTACKER_MELEE_COORD = HexCoord(5, 5)
DEFENDER_MELEE_COORD = HexCoord(6, 5)


@dataclass(frozen=True, slots=True)
class BattleUntilDefeatResult:
    initial_estimate: ArmyMatchupEstimate
    battle: Battle
    combat_log: CombatLog
    turns_taken: int
    rounds_completed: int
    winner: CombatSide | None


def run_demo_battle_until_defeat(
    attacker_army_path: Path = DEFAULT_ATTACKER_ARMY_PATH,
    defender_army_path: Path = DEFAULT_DEFENDER_ARMY_PATH,
) -> BattleUntilDefeatResult:
    catalog = load_packaged_unit_catalog()
    hero_catalog = load_packaged_hero_catalog()
    attacker = load_army_file(attacker_army_path, catalog, hero_catalog)
    defender = load_army_file(defender_army_path, catalog, hero_catalog)
    initial_estimate = estimate_army_matchup(attacker=attacker, defender=defender)
    battle = _battle_from_armies(attacker, defender)
    stack_ids = tuple(battle.unit_stacks)
    combat_log = CombatLog()
    combat_log.record_battle_started()
    turns_taken, rounds_completed = _resolve_battle_until_defeat(battle, combat_log, stack_ids)
    result = BattleUntilDefeatResult(
        initial_estimate=initial_estimate,
        battle=battle,
        combat_log=combat_log,
        turns_taken=turns_taken,
        rounds_completed=rounds_completed,
        winner=_winner(battle),
    )
    _print_result(result, attacker_army_path, defender_army_path)
    return result


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Print a simplified army battle calculation until one side is defeated.")
    parser.add_argument(
        "attacker_army",
        nargs="?",
        type=Path,
        default=DEFAULT_ATTACKER_ARMY_PATH,
    )
    parser.add_argument(
        "defender_army",
        nargs="?",
        type=Path,
        default=DEFAULT_DEFENDER_ARMY_PATH,
    )
    args = parser.parse_args(argv)
    run_demo_battle_until_defeat(args.attacker_army, args.defender_army)


def _battle_from_armies(attacker: Army, defender: Army) -> Battle:
    unit_stacks = {stack.id: stack for stack in (*attacker.stacks, *defender.stacks)}
    if len(unit_stacks) != len(attacker.stacks) + len(defender.stacks):
        msg = "Attacker and defender armies must not use duplicate unit stack IDs"
        raise ValueError(msg)

    battlefield = Battlefield.default()
    occupancy = Occupancy(blocked_coordinates=battlefield.blocked_coordinates)
    reserved_coords = {ATTACKER_MELEE_COORD, DEFENDER_MELEE_COORD}
    available_coords = (coord for coord in battlefield.coordinates() if coord not in reserved_coords)
    for stack_id in unit_stacks:
        occupancy.place(stack_id, next(available_coords))
    heroes = {army.side: army.hero for army in (attacker, defender) if army.hero is not None}
    return Battle(battlefield=battlefield, occupancy=occupancy, unit_stacks=unit_stacks, heroes=heroes)


def _resolve_battle_until_defeat(battle: Battle, combat_log: CombatLog, stack_ids: tuple[str, ...]) -> tuple[int, int]:
    turns_taken = 0
    rounds_completed = 0
    round_number = 1
    while not one_side_defeated(battle):
        round_state = CombatRoundState(round_number=round_number)
        turn_number = 1
        round_had_turn = False
        for actor_id in order_stacks_for_round(battle, stack_ids):
            if actor_id not in battle.unit_stacks:
                continue
            if one_side_defeated(battle):
                break
            opponent_id = _first_living_opponent(battle, actor_id, stack_ids)
            if opponent_id is None:
                break
            _place_melee_pair(battle, actor_id, opponent_id)
            apply_melee_attack_action(
                battle=battle,
                combat_log=combat_log,
                turn=round_state.turn_marker(turn_number),
                attacker_id=actor_id,
                defender_id=opponent_id,
                damage_chooser=_average_damage,
                round_state=round_state,
            )
            turns_taken += 1
            turn_number += 1
            round_had_turn = True
        if not round_had_turn:
            break
        rounds_completed += 1
        round_number += 1
    return turns_taken, rounds_completed


def _first_living_opponent(battle: Battle, actor_id: str, stack_ids: tuple[str, ...]) -> str | None:
    actor = battle.stack(actor_id)
    for stack_id in stack_ids:
        if stack_id in battle.unit_stacks and battle.stack(stack_id).side is not actor.side:
            return stack_id
    return None


def _place_melee_pair(battle: Battle, attacker_id: str, defender_id: str) -> None:
    for coord in (ATTACKER_MELEE_COORD, DEFENDER_MELEE_COORD):
        occupant_id = battle.occupancy.unit_at(coord)
        if occupant_id is not None:
            battle.occupancy.remove(occupant_id)
    battle.occupancy.remove(attacker_id)
    battle.occupancy.remove(defender_id)
    battle.occupancy.place(attacker_id, ATTACKER_MELEE_COORD)
    battle.occupancy.place(defender_id, DEFENDER_MELEE_COORD)


def _average_damage(damage: DamageRange) -> int:
    return (damage.minimum + damage.maximum) // 2


def _winner(battle: Battle) -> CombatSide | None:
    living_sides = {stack.side for stack in battle.unit_stacks.values()}
    if len(living_sides) == 1:
        return next(iter(living_sides))
    return None


def _print_result(result: BattleUntilDefeatResult, attacker_path: Path, defender_path: Path) -> None:
    print("Initial army matchup estimate")
    _print_estimate(result.initial_estimate, attacker_path, defender_path)
    print()
    print("Final state after battle")
    winner = "none" if result.winner is None else result.winner.value
    print(f"Winner: {winner}")
    print(f"Rounds completed: {result.rounds_completed}")
    print(f"Turns taken: {result.turns_taken}")
    _print_battle_side("Attacker", summarize_army(army_from_battle_side(result.battle, CombatSide.ATTACKER)), result.battle)
    _print_battle_side("Defender", summarize_army(army_from_battle_side(result.battle, CombatSide.DEFENDER)), result.battle)
    _print_attack_events(result.combat_log)


def _print_estimate(estimate: ArmyMatchupEstimate, attacker_path: Path, defender_path: Path) -> None:
    _print_estimate_side("Attacker", attacker_path, estimate.attacker)
    _print_estimate_side("Defender", defender_path, estimate.defender)
    favored_side = "tie" if estimate.favored_side is None else estimate.favored_side.value
    print(f"Favored side: {favored_side}")


def _print_estimate_side(label: str, path: Path, summary: ArmySummary) -> None:
    print(f"{label}: {path}")
    print(f"  total remaining health: {summary.total_remaining_health}")
    print(f"  average base damage per turn: {summary.total_average_base_damage_per_turn}")
    print("  stacks:")
    for stack in summary.stacks:
        print(
            f"    {stack.stack_id}: {stack.unit_name} x{stack.count}, "
            f"health {stack.remaining_health}, average base damage {stack.average_base_damage}"
        )


def _print_battle_side(label: str, summary: ArmySummary, battle: Battle) -> None:
    print(f"{label}:")
    if not summary.stacks:
        print("  defeated")
        return
    for stack_summary in summary.stacks:
        stack = battle.stack(stack_summary.stack_id)
        print(
            f"  {stack.id}: {stack.definition.name} x{stack.count}, "
            f"health {stack_summary.remaining_health}, wound damage {stack.wound_damage}"
        )


def _print_attack_events(combat_log: CombatLog) -> None:
    attack_events = tuple(event for event in combat_log.events if isinstance(event, UnitAttackedEvent))
    print("Attack events:")
    if not attack_events:
        print("  none")
        return
    for event in attack_events:
        print(
            f"  {event.attacker_id} -> {event.defender_id}: "
            f"{event.primary_damage.final_damage} damage, "
            f"{event.primary_damage.creatures_killed} killed"
        )
        if event.counterattack is not None:
            print(
                f"    counterattack: {event.counterattack.final_damage} damage, {event.counterattack.creatures_killed} killed"
            )


if __name__ == "__main__":
    main()
