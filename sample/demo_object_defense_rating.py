import argparse
import csv
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ATTACKER_ARMY_PATH = PROJECT_ROOT / "data" / "army" / "temple.yaml"
DEFAULT_OBJECTS_DIR = PROJECT_ROOT / "data" / "object"

if __package__ in {None, ""} and str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from olden.combat.sides import CombatSide  # noqa: E402
from sample.demo_breakpoint_scan import BreakpointScanOutcome, BreakpointScanResult, run_demo_breakpoint_scan  # noqa: E402

OutputFormat = Literal["table", "csv", "json"]


@dataclass(frozen=True, slots=True)
class ObjectDefenseRating:
    object_path: Path
    result: BreakpointScanResult | None
    difficulty: str
    error: str | None = None


def rate_object_defenses(
    attacker_army_path: Path = DEFAULT_ATTACKER_ARMY_PATH,
    objects_dir: Path = DEFAULT_OBJECTS_DIR,
    scanned_stack_id: str | None = None,
    max_count: int | None = None,
) -> tuple[ObjectDefenseRating, ...]:
    ratings = tuple(
        _rate_object_defense(
            attacker_army_path=attacker_army_path,
            object_path=object_path,
            scanned_stack_id=scanned_stack_id,
            max_count=max_count,
        )
        for object_path in _object_army_paths(objects_dir)
    )
    return tuple(sorted(ratings, key=_hardest_first_key))


def print_ratings(ratings: Sequence[ObjectDefenseRating], output_format: OutputFormat = "table") -> None:
    if output_format == "json":
        print(json.dumps([_rating_row(rating) for rating in ratings], indent=2))
        return
    if output_format == "csv":
        writer = csv.DictWriter(sys.stdout, fieldnames=tuple(_rating_row_fields()))
        writer.writeheader()
        writer.writerows(_rating_row(rating) for rating in ratings)
        return
    _print_table(ratings)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Rate object defender armies against an attacker army breakpoint scan.")
    parser.add_argument("--attacker", type=Path, default=DEFAULT_ATTACKER_ARMY_PATH, help="Attacker army YAML path.")
    parser.add_argument(
        "--objects-dir",
        type=Path,
        default=DEFAULT_OBJECTS_DIR,
        help="Directory of defender object YAML files.",
    )
    parser.add_argument("--stack-id", default=None, help="Attacker stack ID to vary. Defaults to the first attacker stack.")
    parser.add_argument("--max-count", type=int, default=None, help="Maximum scanned count. Defaults to the YAML count.")
    parser.add_argument("--format", choices=("table", "csv", "json"), default="table", help="Output format.")
    args = parser.parse_args(argv)
    ratings = rate_object_defenses(
        attacker_army_path=args.attacker,
        objects_dir=args.objects_dir,
        scanned_stack_id=args.stack_id,
        max_count=args.max_count,
    )
    print_ratings(ratings, output_format=args.format)


def _rate_object_defense(
    attacker_army_path: Path,
    object_path: Path,
    scanned_stack_id: str | None,
    max_count: int | None,
) -> ObjectDefenseRating:
    try:
        result = run_demo_breakpoint_scan(
            attacker_army_path=attacker_army_path,
            defender_army_path=object_path,
            scanned_stack_id=scanned_stack_id,
            max_count=max_count,
            neighbors=0,
            print_result=False,
        )
    except Exception as exc:
        return ObjectDefenseRating(object_path=object_path, result=None, difficulty="error", error=str(exc))
    return ObjectDefenseRating(object_path=object_path, result=result, difficulty=_difficulty_label(result))


def _object_army_paths(objects_dir: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in objects_dir.glob("*.yaml") if path.is_file()))


def _hardest_first_key(rating: ObjectDefenseRating) -> tuple[int, int, int, int, str]:
    if rating.result is None:
        return (2, 0, 0, 0, rating.object_path.name)
    breakpoint_count = rating.result.first_winning_count
    decisive_outcome = _decisive_outcome(rating.result)
    attacker_health = decisive_outcome.attacker_remaining_health if decisive_outcome is not None else 0
    attacker_units = decisive_outcome.attacker_remaining_units if decisive_outcome is not None else 0
    if breakpoint_count is None:
        return (0, -rating.result.max_count, attacker_units, attacker_health, rating.object_path.name)
    return (1, -breakpoint_count, attacker_units, attacker_health, rating.object_path.name)


def _difficulty_label(result: BreakpointScanResult) -> str:
    if result.first_winning_count is None:
        return "unbeaten_up_to_max"
    ratio = result.first_winning_count / result.max_count
    if ratio >= 0.75:
        return "hard"
    if ratio >= 0.5:
        return "medium"
    return "easy"


def _print_table(ratings: Sequence[ObjectDefenseRating]) -> None:
    print("Object defense rating")
    print("object, difficulty, first attacker-winning count, max count, winner at max, attacker units, defender units, error")
    for rating in ratings:
        row = _rating_row(rating)
        print(
            f"{row['object']}, {row['difficulty']}, {row['first_winning_count']}, {row['max_count']}, "
            f"{row['winner_at_max']}, {row['attacker_remaining_units']}, {row['defender_remaining_units']}, "
            f"{row['error']}"
        )


def _rating_row(rating: ObjectDefenseRating) -> dict[str, str | int]:
    if rating.result is None:
        return {
            "object": rating.object_path.name,
            "path": str(rating.object_path),
            "difficulty": rating.difficulty,
            "scanned_stack_id": "none",
            "first_winning_count": "none",
            "max_count": 0,
            "winner_at_max": "none",
            "attacker_remaining_units": 0,
            "attacker_remaining_health": 0,
            "defender_remaining_units": 0,
            "defender_remaining_health": 0,
            "rounds_completed": 0,
            "turns_taken": 0,
            "error": rating.error or "unknown error",
        }
    decisive_outcome = _decisive_outcome(rating.result)
    final_outcome = rating.result.outcomes[-1] if rating.result.outcomes else None
    return {
        "object": rating.object_path.name,
        "path": str(rating.object_path),
        "difficulty": rating.difficulty,
        "scanned_stack_id": rating.result.scanned_stack_id,
        "first_winning_count": _count_label(rating.result.first_winning_count),
        "max_count": rating.result.max_count,
        "winner_at_max": _winner_label(final_outcome.winner if final_outcome is not None else None),
        "attacker_remaining_units": decisive_outcome.attacker_remaining_units if decisive_outcome is not None else 0,
        "attacker_remaining_health": decisive_outcome.attacker_remaining_health if decisive_outcome is not None else 0,
        "defender_remaining_units": decisive_outcome.defender_remaining_units if decisive_outcome is not None else 0,
        "defender_remaining_health": decisive_outcome.defender_remaining_health if decisive_outcome is not None else 0,
        "rounds_completed": decisive_outcome.rounds_completed if decisive_outcome is not None else 0,
        "turns_taken": decisive_outcome.turns_taken if decisive_outcome is not None else 0,
        "error": "",
    }


def _rating_row_fields() -> tuple[str, ...]:
    return (
        "object",
        "path",
        "difficulty",
        "scanned_stack_id",
        "first_winning_count",
        "max_count",
        "winner_at_max",
        "attacker_remaining_units",
        "attacker_remaining_health",
        "defender_remaining_units",
        "defender_remaining_health",
        "rounds_completed",
        "turns_taken",
        "error",
    )


def _decisive_outcome(result: BreakpointScanResult) -> BreakpointScanOutcome | None:
    target_count = result.first_winning_count if result.first_winning_count is not None else result.max_count
    for outcome in result.outcomes:
        if outcome.count == target_count:
            return outcome
    return None


def _count_label(count: int | None) -> int | str:
    if count is None:
        return "none"
    return count


def _winner_label(winner: CombatSide | None) -> str:
    if winner is None:
        return "none"
    return winner.value


if __name__ == "__main__":
    main()
