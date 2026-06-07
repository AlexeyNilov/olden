from olden.combat.combat_log import UnitAttackedEvent, load_combat_log_file
from sample.demo_simulation import run_demo_simulation


def test_demo_simulation_writes_loadable_combat_log(tmp_path):
    combat_log_path = tmp_path / "demo_combat_log.yaml"

    result = run_demo_simulation(combat_log_path=combat_log_path, seed=1)
    loaded_log = load_combat_log_file(combat_log_path)

    assert loaded_log.events == result.combat_log.events
    assert any(isinstance(event, UnitAttackedEvent) for event in loaded_log.events)
