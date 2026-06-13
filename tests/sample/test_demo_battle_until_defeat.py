from pathlib import Path

from olden.combat.combat_log import UnitAttackedEvent
from olden.combat.sides import CombatSide
from sample import demo_battle_until_defeat
from sample.demo_battle_until_defeat import BattleUntilDefeatResult, run_demo_battle_until_defeat


def test_demo_battle_until_defeat_prints_initial_estimate_and_final_state(capsys, tmp_path):
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

    result = run_demo_battle_until_defeat(attacker_path, defender_path)

    output = capsys.readouterr().out
    assert isinstance(result, BattleUntilDefeatResult)
    assert result.initial_estimate.attacker_total_remaining_health > 0
    assert result.rounds_completed >= 1
    assert result.turns_taken >= result.rounds_completed
    assert result.winner is not None
    assert "Initial army matchup estimate" in output
    assert "Final state after battle" in output
    assert "Winner:" in output
    assert "Rounds completed:" in output
    assert "Attack events:" in output
    assert "defeated" in output


def test_demo_battle_until_defeat_uses_existing_initiative_order(capsys, tmp_path):
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
  - id: defender-griffin
    unit_id: griffin
    count: 1
""",
    )

    result = run_demo_battle_until_defeat(attacker_path, defender_path)

    attack_events = [event for event in result.combat_log.events if isinstance(event, UnitAttackedEvent)]
    assert attack_events[0].attacker_id == "defender-griffin"
    assert "defender-griffin -> attacker-esquire" in capsys.readouterr().out


def test_demo_battle_until_defeat_main_uses_argument_paths(monkeypatch, tmp_path):
    attacker_path = tmp_path / "attacker.yaml"
    defender_path = tmp_path / "defender.yaml"
    captured_paths: dict[str, Path] = {}

    def run_with_captured_paths(attacker_army_path: Path, defender_army_path: Path) -> BattleUntilDefeatResult:
        captured_paths["attacker"] = attacker_army_path
        captured_paths["defender"] = defender_army_path
        return BattleUntilDefeatResult(
            initial_estimate=demo_battle_until_defeat.estimate_army_matchup(
                attacker=demo_battle_until_defeat.Army(side=CombatSide.ATTACKER, stacks=()),
                defender=demo_battle_until_defeat.Army(side=CombatSide.DEFENDER, stacks=()),
            ),
            battle=demo_battle_until_defeat.Battle(
                battlefield=demo_battle_until_defeat.Battlefield.default(),
                occupancy=demo_battle_until_defeat.Occupancy(),
                unit_stacks={},
            ),
            combat_log=demo_battle_until_defeat.CombatLog(),
            turns_taken=0,
            rounds_completed=0,
            winner=None,
        )

    monkeypatch.setattr(demo_battle_until_defeat, "run_demo_battle_until_defeat", run_with_captured_paths)

    demo_battle_until_defeat.main([str(attacker_path), str(defender_path)])

    assert captured_paths == {"attacker": attacker_path, "defender": defender_path}


def _write_army(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path
