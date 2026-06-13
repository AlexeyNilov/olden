from pathlib import Path

from olden.combat.army import ArmyMatchupEstimate, ArmySummary
from olden.combat.sides import CombatSide
from sample import demo_army_matchup
from sample.demo_army_matchup import run_demo_army_matchup


def test_demo_army_matchup_loads_two_armies_and_prints_estimate(capsys, tmp_path):
    attacker_path = _write_army(
        tmp_path / "attacker.yaml",
        """\
schema_version: 1
side: attacker
unit_stacks:
  - id: attacker-esquire
    unit_id: esquire
    count: 20
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
    count: 2
""",
    )

    estimate = run_demo_army_matchup(attacker_path, defender_path)

    output = capsys.readouterr().out
    assert isinstance(estimate, ArmyMatchupEstimate)
    assert estimate.attacker_total_remaining_health > 0
    assert estimate.defender_total_remaining_health > 0
    assert estimate.attacker_average_base_damage_per_turn > 0
    assert estimate.defender_average_base_damage_per_turn > 0
    assert "Army matchup estimate" in output
    assert f"Attacker: {attacker_path}" in output
    assert f"Defender: {defender_path}" in output
    assert "total remaining health:" in output
    assert "average base damage per turn:" in output
    assert "Favored side:" in output
    assert "Swordsman" in output
    assert "Couatl" in output


def test_demo_army_matchup_main_uses_argument_paths(monkeypatch, tmp_path):
    attacker_path = tmp_path / "attacker.yaml"
    defender_path = tmp_path / "defender.yaml"
    captured_paths: dict[str, Path] = {}

    def run_with_captured_paths(attacker_army_path: Path, defender_army_path: Path) -> ArmyMatchupEstimate:
        captured_paths["attacker"] = attacker_army_path
        captured_paths["defender"] = defender_army_path
        return _estimate_stub()

    monkeypatch.setattr(demo_army_matchup, "run_demo_army_matchup", run_with_captured_paths)

    demo_army_matchup.main([str(attacker_path), str(defender_path)])

    assert captured_paths == {"attacker": attacker_path, "defender": defender_path}


def _write_army(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _estimate_stub() -> ArmyMatchupEstimate:
    attacker = ArmySummary(
        side=CombatSide.ATTACKER,
        stacks=(),
        total_remaining_health=0,
        total_average_base_damage_per_turn=0,
    )
    defender = ArmySummary(
        side=CombatSide.DEFENDER,
        stacks=(),
        total_remaining_health=0,
        total_average_base_damage_per_turn=0,
    )
    return ArmyMatchupEstimate(
        attacker=attacker,
        defender=defender,
        attacker_total_remaining_health=0,
        defender_total_remaining_health=0,
        attacker_average_base_damage_per_turn=0,
        defender_average_base_damage_per_turn=0,
        favored_side=None,
    )
