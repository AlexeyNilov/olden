from pathlib import Path

from olden.combat.army import Army
from olden.combat.combat_log import UnitAttackedEvent
from olden.combat.heroes import Hero, HeroStats
from olden.combat.sides import CombatSide
from olden.combat.units import AttackCategory, DamageRange, UnitCombatStats, UnitDefinition, UnitStack
from sample import demo_one_round_battle
from sample.demo_one_round_battle import OneRoundBattleResult, run_demo_one_round_battle


def test_demo_one_round_battle_prints_initial_estimate_and_resulting_state(capsys, tmp_path):
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

    result = run_demo_one_round_battle(attacker_path, defender_path)

    output = capsys.readouterr().out
    assert isinstance(result, OneRoundBattleResult)
    assert result.initial_estimate.attacker_total_remaining_health > 0
    assert result.turns_taken == 2
    assert "Initial army matchup estimate" in output
    assert "Resulting state after one round" in output
    assert "Attack events:" in output
    assert "attacker-esquire -> defender-coatl" in output
    assert "Defender:" in output
    assert "Couatl" in output


def test_demo_one_round_battle_uses_existing_initiative_order(capsys, tmp_path):
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

    result = run_demo_one_round_battle(attacker_path, defender_path)

    attack_events = [event for event in result.combat_log.events if isinstance(event, UnitAttackedEvent)]
    assert attack_events[0].attacker_id == "defender-griffin"
    assert "defender-griffin -> attacker-esquire" in capsys.readouterr().out


def test_battle_from_armies_preserves_attacker_and_defender_heroes():
    attacker_hero = Hero(id="attacker-hero", name="Attacker", stats=HeroStats(attack=2))
    defender_hero = Hero(id="defender-hero", name="Defender", stats=HeroStats(defense=3))
    attacker = Army(
        side=CombatSide.ATTACKER,
        stacks=(_stack("attacker-esquire", CombatSide.ATTACKER),),
        hero=attacker_hero,
    )
    defender = Army(
        side=CombatSide.DEFENDER,
        stacks=(_stack("defender-esquire", CombatSide.DEFENDER),),
        hero=defender_hero,
    )

    battle = demo_one_round_battle._battle_from_armies(attacker, defender)

    assert battle.heroes == {
        CombatSide.ATTACKER: attacker_hero,
        CombatSide.DEFENDER: defender_hero,
    }


def test_demo_one_round_battle_main_uses_argument_paths(monkeypatch, tmp_path):
    attacker_path = tmp_path / "attacker.yaml"
    defender_path = tmp_path / "defender.yaml"
    captured_paths: dict[str, Path] = {}

    def run_with_captured_paths(attacker_army_path: Path, defender_army_path: Path) -> OneRoundBattleResult:
        captured_paths["attacker"] = attacker_army_path
        captured_paths["defender"] = defender_army_path
        return OneRoundBattleResult(
            initial_estimate=demo_one_round_battle.estimate_army_matchup(
                attacker=demo_one_round_battle.Army(side=demo_one_round_battle.CombatSide.ATTACKER, stacks=()),
                defender=demo_one_round_battle.Army(side=demo_one_round_battle.CombatSide.DEFENDER, stacks=()),
            ),
            battle=demo_one_round_battle.Battle(
                battlefield=demo_one_round_battle.Battlefield.default(),
                occupancy=demo_one_round_battle.Occupancy(),
                unit_stacks={},
            ),
            combat_log=demo_one_round_battle.CombatLog(),
            turns_taken=0,
        )

    monkeypatch.setattr(demo_one_round_battle, "run_demo_one_round_battle", run_with_captured_paths)

    demo_one_round_battle.main([str(attacker_path), str(defender_path)])

    assert captured_paths == {"attacker": attacker_path, "defender": defender_path}


def _write_army(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _stack(stack_id: str, side: CombatSide) -> UnitStack:
    return UnitStack(
        id=stack_id,
        definition=UnitDefinition(
            id="esquire",
            name="Swordsman",
            initiative=5,
            speed=4,
            combat=UnitCombatStats(
                health=12,
                attack=4,
                defense=4,
                damage=DamageRange(minimum=2, maximum=3),
                attack_category=AttackCategory.MELEE,
            ),
        ),
        side=side,
        count=10,
    )
