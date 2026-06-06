import pytest

from olden.combat.battle_setup import load_battle_initial_state_yaml
from olden.combat.combat_log import (
    CombatLog,
    CombatLogValidationError,
    TurnMarker,
    UnitMovedEvent,
    dump_combat_log_yaml,
    load_combat_log_file,
    load_combat_log_yaml,
    replay_combat_log,
    save_combat_log_file,
)
from olden.combat.coordinates import HexCoord
from olden.unit_data.packaged import load_packaged_unit_catalog

VALID_INITIAL_STATE_YAML = """
schema_version: 1
battlefield:
  obstacles: []
unit_stacks:
  - id: player-esquire
    unit_id: esquire
    side: player
    count: 10
    anchor:
      column: 0
      row: 5
  - id: enemy-esquire
    unit_id: esquire
    side: enemy
    count: 20
    anchor:
      column: 12
      row: 5
"""


def test_combat_log_records_unit_movement_with_replayable_path():
    catalog = load_packaged_unit_catalog()
    battle = load_battle_initial_state_yaml(VALID_INITIAL_STATE_YAML, catalog)
    combat_log = CombatLog()

    movement = battle.move_stack("player-esquire", HexCoord(2, 5))
    combat_log.record_unit_moved(TurnMarker(round_number=1, turn_number=1), movement)

    event = combat_log.events[0]
    assert isinstance(event, UnitMovedEvent)
    assert event.sequence == 1
    assert event.stack_id == "player-esquire"
    assert event.start == HexCoord(0, 5)
    assert event.destination == HexCoord(2, 5)
    assert event.path == (HexCoord(0, 5), HexCoord(1, 5), HexCoord(2, 5))


def test_combat_log_yaml_round_trips_movement_events():
    catalog = load_packaged_unit_catalog()
    battle = load_battle_initial_state_yaml(VALID_INITIAL_STATE_YAML, catalog)
    combat_log = CombatLog()
    combat_log.record_battle_started()
    combat_log.record_unit_moved(TurnMarker(round_number=1, turn_number=1), battle.move_stack("player-esquire", HexCoord(2, 5)))

    loaded_log = load_combat_log_yaml(dump_combat_log_yaml(combat_log))

    assert loaded_log.events == combat_log.events


def test_combat_log_file_writes_loadable_yaml(tmp_path):
    combat_log = CombatLog()
    combat_log.record_battle_started()
    path = tmp_path / "combat-log.yaml"

    save_combat_log_file(path, combat_log)
    loaded_log = load_combat_log_file(path)

    assert loaded_log.events == combat_log.events


def test_load_combat_log_yaml_rejects_noncontiguous_event_sequences():
    content = """
schema_version: 1
events:
  - sequence: 2
    type: battle_started
"""

    with pytest.raises(CombatLogValidationError, match="contiguous"):
        load_combat_log_yaml(content)


def test_replay_combat_log_reconstructs_final_occupancy():
    catalog = load_packaged_unit_catalog()
    initial_battle = load_battle_initial_state_yaml(VALID_INITIAL_STATE_YAML, catalog)
    executed_battle = load_battle_initial_state_yaml(VALID_INITIAL_STATE_YAML, catalog)
    combat_log = CombatLog()
    combat_log.record_unit_moved(
        TurnMarker(round_number=1, turn_number=1),
        executed_battle.move_stack("player-esquire", HexCoord(2, 5)),
    )

    replayed = replay_combat_log(initial_battle, combat_log)

    assert replayed.occupancy.unit_at(HexCoord(0, 5)) is None
    assert replayed.occupancy.unit_at(HexCoord(2, 5)) == "player-esquire"
    assert replayed.occupancy.unit_at(HexCoord(12, 5)) == "enemy-esquire"


def test_replay_combat_log_rejects_movement_that_does_not_match_logged_path():
    catalog = load_packaged_unit_catalog()
    initial_battle = load_battle_initial_state_yaml(VALID_INITIAL_STATE_YAML, catalog)
    combat_log = CombatLog(
        events=(
            UnitMovedEvent(
                sequence=1,
                turn=TurnMarker(round_number=1, turn_number=1),
                stack_id="player-esquire",
                start=HexCoord(0, 5),
                destination=HexCoord(2, 5),
                path=(HexCoord(0, 5), HexCoord(2, 5)),
            ),
        )
    )

    with pytest.raises(CombatLogValidationError, match="movement"):
        replay_combat_log(initial_battle, combat_log)
