from olden.combat.battle_setup import load_battle_initial_state_file
from olden.combat.combat_log import load_combat_log_file, replay_combat_log
from olden.unit_data.packaged import load_packaged_unit_catalog
from sample.genetic_strategy_discovery import run_genetic_strategy_discovery


def test_genetic_strategy_discovery_writes_replayable_best_battle_and_combat_log(tmp_path):
    best_battle_path = tmp_path / "genetic_best_battle.yaml"
    best_combat_log_path = tmp_path / "genetic_best_combat_log.yaml"

    result = run_genetic_strategy_discovery(
        best_battle_path=best_battle_path,
        best_combat_log_path=best_combat_log_path,
        seed=3,
        population_size=8,
        generations=3,
    )
    best_battle = load_battle_initial_state_file(best_battle_path, load_packaged_unit_catalog())
    best_combat_log = load_combat_log_file(best_combat_log_path)
    replayed_battle = replay_combat_log(best_battle, best_combat_log)

    assert best_battle_path.exists()
    assert best_combat_log_path.exists()
    assert sum(stack.count for stack in best_battle.unit_stacks.values() if stack.side.value == "player") == 10
    assert best_combat_log.events == result.combat_result.combat_log.events
    assert replayed_battle.unit_stacks == result.combat_result.battle.unit_stacks
