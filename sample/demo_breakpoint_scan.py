import argparse
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from olden.combat.action_opportunities import CombatRoundState
from olden.combat.army import Army, army_from_battle_side, summarize_army
from olden.combat.army_setup import load_army_file
from olden.combat.battle import Battle
from olden.combat.battlefield import Battlefield
from olden.combat.combat_actions import apply_melee_attack_action
from olden.combat.combat_log import CombatLog
from olden.combat.coordinates import HexCoord
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.targeting import one_side_defeated
from olden.combat.turn_order import order_stacks_for_round
from olden.combat.units import DamageRange, UnitStack
from olden.hero_data.packaged import load_packaged_hero_catalog
from olden.unit_data.packaged import load_packaged_unit_catalog

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ATTACKER_ARMY_PATH = PROJECT_ROOT / "data" / "army" / "temple.yaml"
DEFAULT_DEFENDER_ARMY_PATH = PROJECT_ROOT / "data" / "object" / "altar_of_meareas.yaml"
ATTACKER_MELEE_COORD = HexCoord(5, 5)
DEFENDER_MELEE_COORD = HexCoord(6, 5)


@dataclass(frozen=True, slots=True)
class BreakpointScanOutcome:
    count: int
    winner: CombatSide | None
    rounds_completed: int
    turns_taken: int
    attacker_remaining_units: int
    attacker_remaining_health: int
    defender_remaining_units: int
    defender_remaining_health: int


@dataclass(frozen=True, slots=True)
class BreakpointScanResult:
    scanned_stack_id: str
    max_count: int
    first_winning_count: int | None
    outcomes: tuple[BreakpointScanOutcome, ...]


def run_demo_breakpoint_scan(
    attacker_army_path: Path = DEFAULT_ATTACKER_ARMY_PATH,
    defender_army_path: Path = DEFAULT_DEFENDER_ARMY_PATH,
    scanned_stack_id: str | None = None,
    max_count: int | None = None,
    neighbors: int = 3,
) -> BreakpointScanResult:
    catalog = load_packaged_unit_catalog()
    hero_catalog = load_packaged_hero_catalog()
    attacker = load_army_file(attacker_army_path, catalog, hero_catalog)
    defender = load_army_file(defender_army_path, catalog, hero_catalog)
    stack_id = scanned_stack_id or _first_stack_id(attacker)
    stack = _stack_by_id(attacker, stack_id)
    resolved_max_count = max_count if max_count is not None else stack.count
    if resolved_max_count < 1:
        msg = "Maximum scanned count must be positive"
        raise ValueError(msg)
    if neighbors < 0:
        msg = "Neighbor count must not be negative"
        raise ValueError(msg)

    outcomes = tuple(_scan_count(attacker, defender, stack_id, count) for count in range(1, resolved_max_count + 1))
    first_winning_count = _first_winning_count(outcomes)
    result = BreakpointScanResult(
        scanned_stack_id=stack_id,
        max_count=resolved_max_count,
        first_winning_count=first_winning_count,
        outcomes=outcomes,
    )
    _print_result(result, neighbors)
    return result


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Scan attacker stack counts for a simplified battle breakpoint.")
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
    parser.add_argument("--stack-id", default=None, help="Attacker stack ID to vary. Defaults to the first attacker stack.")
    parser.add_argument("--max-count", type=int, default=None, help="Maximum stack count to scan. Defaults to the YAML count.")
    parser.add_argument("--neighbors", type=int, default=3, help="Number of counts to print on each side of the breakpoint.")
    args = parser.parse_args(argv)
    run_demo_breakpoint_scan(
        args.attacker_army,
        args.defender_army,
        scanned_stack_id=args.stack_id,
        max_count=args.max_count,
        neighbors=args.neighbors,
    )


def _scan_count(attacker: Army, defender: Army, stack_id: str, count: int) -> BreakpointScanOutcome:
    battle = _battle_from_armies(_with_stack_count(attacker, stack_id, count), defender)
    combat_log = CombatLog()
    combat_log.record_battle_started()
    turns_taken, rounds_completed = _resolve_battle_until_defeat(battle, combat_log, tuple(battle.unit_stacks))
    attacker_summary = summarize_army(army_from_battle_side(battle, CombatSide.ATTACKER))
    defender_summary = summarize_army(army_from_battle_side(battle, CombatSide.DEFENDER))
    return BreakpointScanOutcome(
        count=count,
        winner=_winner(battle),
        rounds_completed=rounds_completed,
        turns_taken=turns_taken,
        attacker_remaining_units=sum(stack.count for stack in battle.unit_stacks.values() if stack.side is CombatSide.ATTACKER),
        attacker_remaining_health=attacker_summary.total_remaining_health,
        defender_remaining_units=sum(stack.count for stack in battle.unit_stacks.values() if stack.side is CombatSide.DEFENDER),
        defender_remaining_health=defender_summary.total_remaining_health,
    )


def _battle_from_armies(attacker: Army, defender: Army) -> Battle:
    unit_stacks = {stack.id: stack for stack in (*attacker.stacks, *defender.stacks)}
    if len(unit_stacks) != len(attacker.stacks) + len(defender.stacks):
        msg = "Attacker and defender armies must not use duplicate unit stack IDs"
        raise ValueError(msg)

    battlefield = Battlefield.default()
    occupancy = Occupancy(blocked_coordinates=battlefield.blocked_coordinates)
    reserved_coords = {ATTACKER_MELEE_COORD, DEFENDER_MELEE_COORD}
    available_coords = (coord for coord in battlefield.coordinates() if coord not in reserved_coords)
    for unit_stack_id in unit_stacks:
        occupancy.place(unit_stack_id, next(available_coords))
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


def _with_stack_count(army: Army, stack_id: str, count: int) -> Army:
    return Army(
        side=army.side,
        stacks=tuple(_replace_count(stack, count) if stack.id == stack_id else stack for stack in army.stacks),
        hero=army.hero,
    )


def _replace_count(stack: UnitStack, count: int) -> UnitStack:
    return replace(stack, count=count, wound_damage=0)


def _first_stack_id(army: Army) -> str:
    if not army.stacks:
        msg = "Attacker army must contain at least one unit stack"
        raise ValueError(msg)
    return army.stacks[0].id


def _stack_by_id(army: Army, stack_id: str) -> UnitStack:
    for stack in army.stacks:
        if stack.id == stack_id:
            return stack
    msg = f"Attacker army does not contain unit stack: {stack_id}"
    raise ValueError(msg)


def _first_winning_count(outcomes: tuple[BreakpointScanOutcome, ...]) -> int | None:
    for outcome in outcomes:
        if outcome.winner is CombatSide.ATTACKER:
            return outcome.count
    return None


def _print_result(result: BreakpointScanResult, neighbors: int) -> None:
    print("Breakpoint scan")
    print(f"Scanned stack: {result.scanned_stack_id}")
    print(f"Max count: {result.max_count}")
    if result.first_winning_count is None:
        print(f"First attacker-winning count: none up to {result.max_count}")
    else:
        print(f"First attacker-winning count: {result.first_winning_count}")
    print("Outcomes near breakpoint:")
    for outcome in _nearby_outcomes(result, neighbors):
        print(
            f"  {outcome.count}: winner {_winner_label(outcome.winner)}, "
            f"rounds {outcome.rounds_completed}, turns {outcome.turns_taken}, "
            f"attacker units {outcome.attacker_remaining_units}, defender units {outcome.defender_remaining_units}"
        )


def _nearby_outcomes(result: BreakpointScanResult, neighbors: int) -> tuple[BreakpointScanOutcome, ...]:
    if result.first_winning_count is None:
        return result.outcomes[-(neighbors + 1) :]
    start = max(1, result.first_winning_count - neighbors)
    end = min(result.max_count, result.first_winning_count + neighbors)
    return tuple(outcome for outcome in result.outcomes if start <= outcome.count <= end)


def _winner_label(winner: CombatSide | None) -> str:
    if winner is None:
        return "none"
    return winner.value


if __name__ == "__main__":
    main()
