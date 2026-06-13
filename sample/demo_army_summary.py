from pathlib import Path

from olden.combat.army import ArmySummary, summarize_army
from olden.combat.army_setup import load_army_file
from olden.hero_data.packaged import load_packaged_hero_catalog
from olden.unit_data.packaged import load_packaged_unit_catalog

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARMY_PATH = PROJECT_ROOT / "data" / "demo_army.yaml"


def run_demo_army_summary(army_path: Path = DEFAULT_ARMY_PATH) -> ArmySummary:
    army = load_army_file(army_path, load_packaged_unit_catalog(), load_packaged_hero_catalog())
    summary = summarize_army(army)
    _print_summary(summary)
    return summary


def main() -> None:
    run_demo_army_summary()


def _print_summary(summary: ArmySummary) -> None:
    print(f"Army: {summary.side.value}")
    print(f"Total remaining health: {summary.total_remaining_health}")
    print(f"Average base damage per turn: {summary.total_average_base_damage_per_turn}")
    print("Stacks:")
    for stack in summary.stacks:
        print(
            f"  {stack.stack_id}: {stack.unit_name} x{stack.count}, "
            f"health {stack.remaining_health}, average base damage {stack.average_base_damage}"
        )


if __name__ == "__main__":
    main()
