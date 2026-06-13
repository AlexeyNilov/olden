from pathlib import Path

from olden.combat.sides import CombatSide
from sample import demo_breakpoint_scan
from sample.demo_breakpoint_scan import BreakpointScanResult, run_demo_breakpoint_scan


def test_demo_breakpoint_scan_finds_first_attacker_winning_count(capsys, tmp_path):
    attacker_path = _write_army(
        tmp_path / "attacker.yaml",
        """\
schema_version: 1
side: attacker
unit_stacks:
  - id: attacker-esquire
    unit_id: esquire
    count: 58
""",
    )
    defender_path = _write_army(
        tmp_path / "defender.yaml",
        """\
schema_version: 1
side: defender
unit_stacks:
  - id: defender-coatl
    unit_id: coatl
    count: 3
""",
    )

    result = run_demo_breakpoint_scan(attacker_path, defender_path)

    output = capsys.readouterr().out
    assert isinstance(result, BreakpointScanResult)
    assert result.scanned_stack_id == "attacker-esquire"
    assert result.first_winning_count == 58
    assert result.outcomes[-2].count == 57
    assert result.outcomes[-2].winner is CombatSide.DEFENDER
    assert result.outcomes[-1].count == 58
    assert result.outcomes[-1].winner is CombatSide.ATTACKER
    assert "Breakpoint scan" in output
    assert "Scanned stack: attacker-esquire" in output
    assert "First attacker-winning count: 58" in output
    assert "57: winner defender" in output
    assert "58: winner attacker" in output


def test_demo_breakpoint_scan_reports_when_no_attacker_win_is_found(capsys, tmp_path):
    attacker_path = _write_army(
        tmp_path / "attacker.yaml",
        """\
schema_version: 1
side: attacker
unit_stacks:
  - id: attacker-esquire
    unit_id: esquire
    count: 10
""",
    )
    defender_path = _write_army(
        tmp_path / "defender.yaml",
        """\
schema_version: 1
side: defender
unit_stacks:
  - id: defender-coatl
    unit_id: coatl
    count: 3
""",
    )

    result = run_demo_breakpoint_scan(attacker_path, defender_path)

    assert result.first_winning_count is None
    assert "First attacker-winning count: none up to 10" in capsys.readouterr().out


def test_demo_breakpoint_scan_main_uses_argument_paths_and_options(monkeypatch, tmp_path):
    attacker_path = tmp_path / "attacker.yaml"
    defender_path = tmp_path / "defender.yaml"
    captured: dict[str, object] = {}

    def run_with_captured_args(
        attacker_army_path: Path,
        defender_army_path: Path,
        scanned_stack_id: str | None = None,
        max_count: int | None = None,
        neighbors: int = 3,
    ) -> BreakpointScanResult:
        captured["attacker"] = attacker_army_path
        captured["defender"] = defender_army_path
        captured["stack"] = scanned_stack_id
        captured["max_count"] = max_count
        captured["neighbors"] = neighbors
        return BreakpointScanResult(
            scanned_stack_id=scanned_stack_id or "attacker-esquire",
            max_count=max_count or 0,
            first_winning_count=None,
            outcomes=(),
        )

    monkeypatch.setattr(demo_breakpoint_scan, "run_demo_breakpoint_scan", run_with_captured_args)

    demo_breakpoint_scan.main(
        [str(attacker_path), str(defender_path), "--stack-id", "attacker-esquire", "--max-count", "20", "--neighbors", "2"]
    )

    assert captured == {
        "attacker": attacker_path,
        "defender": defender_path,
        "stack": "attacker-esquire",
        "max_count": 20,
        "neighbors": 2,
    }


def _write_army(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path
