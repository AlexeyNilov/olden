from olden.combat.battle_setup import load_battle_initial_state_file
from olden.combat.combat_log import UnitMovedEvent, load_combat_log_file, replay_combat_log
from olden.unit_data.packaged import load_packaged_unit_catalog
from sample.demo_movement_simulation import (
    DEFAULT_BATTLE_INITIAL_STATE_PATH,
    run_demo_movement_simulation,
)


def test_demo_movement_sample_loads_demo_battle_and_saves_combat_log(tmp_path):
    combat_log_path = tmp_path / "demo_movement_log.yaml"

    result = run_demo_movement_simulation(combat_log_path=combat_log_path, seed=0)

    loaded_log = load_combat_log_file(combat_log_path)
    initial_battle = load_battle_initial_state_file(DEFAULT_BATTLE_INITIAL_STATE_PATH, load_packaged_unit_catalog())
    replayed_battle = replay_combat_log(initial_battle, loaded_log)
    assert combat_log_path.exists()
    assert loaded_log.events == result.combat_log.events
    assert any(isinstance(event, UnitMovedEvent) for event in loaded_log.events)
    assert replayed_battle.occupancy.coordinates_for("player-esquire") == result.battle.occupancy.coordinates_for(
        "player-esquire"
    )
    assert replayed_battle.occupancy.coordinates_for("enemy-esquire") == result.battle.occupancy.coordinates_for(
        "enemy-esquire"
    )
