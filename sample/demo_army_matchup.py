import argparse
from collections.abc import Sequence
from pathlib import Path

from olden.combat.army import ArmyMatchupEstimate, ArmySummary, estimate_army_matchup
from olden.combat.army_setup import load_army_file
from olden.hero_data.packaged import load_packaged_hero_catalog
from olden.unit_data.packaged import load_packaged_unit_catalog

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ATTACKER_ARMY_PATH = PROJECT_ROOT / "data" / "army" / "temple.yaml"
DEFAULT_DEFENDER_ARMY_PATH = PROJECT_ROOT / "data" / "object" / "altar_of_meareas.yaml"


def run_demo_army_matchup(
    attacker_army_path: Path = DEFAULT_ATTACKER_ARMY_PATH,
    defender_army_path: Path = DEFAULT_DEFENDER_ARMY_PATH,
) -> ArmyMatchupEstimate:
    catalog = load_packaged_unit_catalog()
    hero_catalog = load_packaged_hero_catalog()
    attacker = load_army_file(attacker_army_path, catalog, hero_catalog)
    defender = load_army_file(defender_army_path, catalog, hero_catalog)
    estimate = estimate_army_matchup(attacker=attacker, defender=defender)
    _print_estimate(estimate, attacker_army_path, defender_army_path)
    return estimate


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Print a coarse attacker/defender army matchup estimate.")
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
    run_demo_army_matchup(args.attacker_army, args.defender_army)


def _print_estimate(estimate: ArmyMatchupEstimate, attacker_path: Path, defender_path: Path) -> None:
    print("Army matchup estimate")
    _print_side_summary("Attacker", attacker_path, estimate.attacker)
    _print_side_summary("Defender", defender_path, estimate.defender)
    favored_side = "tie" if estimate.favored_side is None else estimate.favored_side.value
    print(f"Favored side: {favored_side}")


def _print_side_summary(label: str, path: Path, summary: ArmySummary) -> None:
    print(f"{label}: {path}")
    print(f"  total remaining health: {summary.total_remaining_health}")
    print(f"  average base damage per turn: {summary.total_average_base_damage_per_turn}")
    print("  stacks:")
    for stack in summary.stacks:
        print(
            f"    {stack.stack_id}: {stack.unit_name} x{stack.count}, "
            f"health {stack.remaining_health}, average base damage {stack.average_base_damage}"
        )


if __name__ == "__main__":
    main()
