from pathlib import Path

from olden.combat.sides import CombatSide
from sample import demo_object_defense_rating
from sample.demo_breakpoint_scan import BreakpointScanOutcome, BreakpointScanResult
from sample.demo_object_defense_rating import ObjectDefenseRating, rate_object_defenses


def test_rate_object_defenses_ranks_hardest_defenders_first(monkeypatch, tmp_path):
    attacker_path = tmp_path / "temple.yaml"
    objects_dir = tmp_path / "object"
    objects_dir.mkdir()
    easy_path = _write_army(objects_dir / "easy.yaml")
    hard_path = _write_army(objects_dir / "hard.yaml")
    unbeaten_path = _write_army(objects_dir / "unbeaten.yaml")

    results = {
        easy_path: _scan_result(first_winning_count=8, max_count=20, winner_at_max=CombatSide.ATTACKER),
        hard_path: _scan_result(first_winning_count=15, max_count=20, winner_at_max=CombatSide.ATTACKER),
        unbeaten_path: _scan_result(first_winning_count=None, max_count=20, winner_at_max=CombatSide.DEFENDER),
    }
    captured: list[tuple[Path, Path, str | None, int | None]] = []

    def scan(
        attacker_army_path: Path,
        defender_army_path: Path,
        scanned_stack_id: str | None = None,
        max_count: int | None = None,
        neighbors: int = 3,
        print_result: bool = True,
    ) -> BreakpointScanResult:
        captured.append((attacker_army_path, defender_army_path, scanned_stack_id, max_count))
        assert neighbors == 0
        assert print_result is False
        return results[defender_army_path]

    monkeypatch.setattr(demo_object_defense_rating, "run_demo_breakpoint_scan", scan)

    ratings = rate_object_defenses(
        attacker_army_path=attacker_path,
        objects_dir=objects_dir,
        scanned_stack_id="attacker-esquire",
        max_count=20,
    )

    assert [rating.object_path.name for rating in ratings] == ["unbeaten.yaml", "hard.yaml", "easy.yaml"]
    assert [rating.difficulty for rating in ratings] == ["unbeaten_up_to_max", "hard", "easy"]
    assert captured == [
        (attacker_path, easy_path, "attacker-esquire", 20),
        (attacker_path, hard_path, "attacker-esquire", 20),
        (attacker_path, unbeaten_path, "attacker-esquire", 20),
    ]


def test_object_defense_rating_prints_table(capsys):
    ratings = (
        ObjectDefenseRating(
            object_path=Path("data/object/unbeaten.yaml"),
            result=_scan_result(first_winning_count=None, max_count=20, winner_at_max=CombatSide.DEFENDER),
            difficulty="unbeaten_up_to_max",
        ),
        ObjectDefenseRating(
            object_path=Path("data/object/hard.yaml"),
            result=_scan_result(first_winning_count=15, max_count=20, winner_at_max=CombatSide.ATTACKER),
            difficulty="hard",
        ),
    )

    demo_object_defense_rating.print_ratings(ratings, output_format="table")

    output = capsys.readouterr().out
    assert "Object defense rating" in output
    assert "unbeaten.yaml" in output
    assert "none" in output
    assert "hard.yaml" in output
    assert "15" in output


def test_rate_object_defenses_reports_scan_errors(monkeypatch, tmp_path):
    attacker_path = tmp_path / "temple.yaml"
    objects_dir = tmp_path / "object"
    objects_dir.mkdir()
    broken_path = _write_army(objects_dir / "broken.yaml")

    def scan(
        attacker_army_path: Path,
        defender_army_path: Path,
        scanned_stack_id: str | None = None,
        max_count: int | None = None,
        neighbors: int = 3,
        print_result: bool = True,
    ) -> BreakpointScanResult:
        raise ValueError("unsupported unit")

    monkeypatch.setattr(demo_object_defense_rating, "run_demo_breakpoint_scan", scan)

    ratings = rate_object_defenses(attacker_army_path=attacker_path, objects_dir=objects_dir)

    assert ratings == (
        ObjectDefenseRating(
            object_path=broken_path,
            result=None,
            difficulty="error",
            error="unsupported unit",
        ),
    )


def test_object_defense_rating_main_uses_arguments(monkeypatch, tmp_path):
    attacker_path = tmp_path / "temple.yaml"
    objects_dir = tmp_path / "object"
    captured: dict[str, object] = {}

    def rate(
        attacker_army_path: Path,
        objects_dir: Path,
        scanned_stack_id: str | None = None,
        max_count: int | None = None,
    ) -> tuple[ObjectDefenseRating, ...]:
        captured["attacker"] = attacker_army_path
        captured["objects_dir"] = objects_dir
        captured["stack"] = scanned_stack_id
        captured["max_count"] = max_count
        return ()

    monkeypatch.setattr(demo_object_defense_rating, "rate_object_defenses", rate)

    demo_object_defense_rating.main(
        [
            "--attacker",
            str(attacker_path),
            "--objects-dir",
            str(objects_dir),
            "--stack-id",
            "attacker-esquire",
            "--max-count",
            "50",
            "--format",
            "json",
        ]
    )

    assert captured == {
        "attacker": attacker_path,
        "objects_dir": objects_dir,
        "stack": "attacker-esquire",
        "max_count": 50,
    }


def _write_army(path: Path) -> Path:
    path.write_text("schema_version: 1\nside: defender\nunit_stacks: []\n", encoding="utf-8")
    return path


def _scan_result(
    first_winning_count: int | None,
    max_count: int,
    winner_at_max: CombatSide | None,
) -> BreakpointScanResult:
    outcomes = tuple(
        BreakpointScanOutcome(
            count=count,
            winner=winner_at_max if count == max_count else CombatSide.DEFENDER,
            rounds_completed=count,
            turns_taken=count * 2,
            attacker_remaining_units=max_count - count,
            attacker_remaining_health=(max_count - count) * 10,
            defender_remaining_units=count,
            defender_remaining_health=count * 10,
        )
        for count in range(1, max_count + 1)
    )
    return BreakpointScanResult(
        scanned_stack_id="attacker-esquire",
        max_count=max_count,
        first_winning_count=first_winning_count,
        outcomes=outcomes,
    )
