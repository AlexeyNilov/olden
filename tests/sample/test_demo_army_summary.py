from olden.combat.army import ArmySummary
from sample.demo_army_summary import run_demo_army_summary


def test_demo_army_summary_loads_army_and_prints_summary(capsys, tmp_path):
    army_path = tmp_path / "army.yaml"
    army_path.write_text(
        """\
schema_version: 1
side: attacker
unit_stacks:
  - id: attacker-esquire
    unit_id: esquire
    count: 20
  - id: attacker-griffin
    unit_id: griffin
    count: 5
  - id: attacker-crossbowman
    unit_id: crossbowman
    count: 12
""",
        encoding="utf-8",
    )

    summary = run_demo_army_summary(army_path)

    output = capsys.readouterr().out
    assert isinstance(summary, ArmySummary)
    assert summary.side.value == "attacker"
    assert summary.total_remaining_health > 0
    assert summary.total_average_base_damage_per_turn > 0
    assert "Army: attacker" in output
    assert "Total remaining health:" in output
    assert "Average base damage per turn:" in output
    assert "Swordsman" in output
    assert "Griffin" in output
    assert "Crossbowman" in output
