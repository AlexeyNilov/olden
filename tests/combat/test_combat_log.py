import pytest

from olden.combat.battle_setup import load_battle_initial_state_yaml
from olden.combat.combat_log import (
    CombatLog,
    CombatLogReplayState,
    CombatLogValidationError,
    TurnMarker,
    UnitAttackedEvent,
    UnitMovedEvent,
    UnitSkippedEvent,
    UnitWaitedEvent,
    apply_combat_log_event,
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
  - id: attacker-esquire
    unit_id: esquire
    side: attacker
    count: 10
    anchor:
      column: 0
      row: 5
  - id: defender-esquire
    unit_id: esquire
    side: defender
    count: 20
    anchor:
      column: 12
      row: 5
"""

ADJACENT_INITIAL_STATE_YAML = """
schema_version: 1
battlefield:
  obstacles: []
unit_stacks:
  - id: attacker-esquire
    unit_id: esquire
    side: attacker
    count: 10
    anchor:
      column: 0
      row: 5
  - id: defender-esquire
    unit_id: esquire
    side: defender
    count: 20
    anchor:
      column: 1
      row: 5
"""


def test_combat_log_records_unit_movement_with_replayable_path():
    catalog = load_packaged_unit_catalog()
    battle = load_battle_initial_state_yaml(VALID_INITIAL_STATE_YAML, catalog)
    combat_log = CombatLog()

    movement = battle.move_stack("attacker-esquire", HexCoord(2, 5))
    combat_log.record_unit_moved(TurnMarker(round_number=1, turn_number=1), movement)

    event = combat_log.events[0]
    assert isinstance(event, UnitMovedEvent)
    assert event.sequence == 1
    assert event.stack_id == "attacker-esquire"
    assert event.start == HexCoord(0, 5)
    assert event.destination == HexCoord(2, 5)
    assert event.path == (HexCoord(0, 5), HexCoord(1, 5), HexCoord(2, 5))


def test_combat_log_yaml_round_trips_movement_events():
    catalog = load_packaged_unit_catalog()
    battle = load_battle_initial_state_yaml(VALID_INITIAL_STATE_YAML, catalog)
    combat_log = CombatLog()
    combat_log.record_battle_started()
    combat_log.record_unit_moved(
        TurnMarker(round_number=1, turn_number=1), battle.move_stack("attacker-esquire", HexCoord(2, 5))
    )

    loaded_log = load_combat_log_yaml(dump_combat_log_yaml(combat_log))

    assert loaded_log.events == combat_log.events


def test_combat_log_records_unit_attack_with_replayable_damage():
    catalog = load_packaged_unit_catalog()
    battle = load_battle_initial_state_yaml(ADJACENT_INITIAL_STATE_YAML, catalog)
    combat_log = CombatLog()

    attack = battle.attack_stack("attacker-esquire", "defender-esquire", damage_chooser=lambda damage: damage.minimum)
    combat_log.record_unit_attacked(TurnMarker(round_number=1, turn_number=1), attack)

    event = combat_log.events[0]
    assert isinstance(event, UnitAttackedEvent)
    assert event.sequence == 1
    assert event.attacker_id == "attacker-esquire"
    assert event.defender_id == "defender-esquire"
    assert event.primary_damage.selected_damage == 2
    assert event.primary_damage.final_damage == 20
    assert event.counterattack is not None
    assert event.counterattack.final_damage == 38


def test_combat_log_yaml_round_trips_attack_events():
    catalog = load_packaged_unit_catalog()
    battle = load_battle_initial_state_yaml(ADJACENT_INITIAL_STATE_YAML, catalog)
    combat_log = CombatLog()
    combat_log.record_battle_started()
    combat_log.record_unit_attacked(
        TurnMarker(round_number=1, turn_number=1),
        battle.attack_stack("attacker-esquire", "defender-esquire", damage_chooser=lambda damage: damage.minimum),
    )

    loaded_log = load_combat_log_yaml(dump_combat_log_yaml(combat_log))

    assert loaded_log.events == combat_log.events


def test_combat_log_yaml_round_trips_wait_and_skip_events():
    combat_log = CombatLog()
    combat_log.record_battle_started()
    combat_log.record_unit_waited(TurnMarker(round_number=1, turn_number=1), "attacker-esquire")
    combat_log.record_unit_skipped(TurnMarker(round_number=1, turn_number=3), "attacker-esquire")

    loaded_log = load_combat_log_yaml(dump_combat_log_yaml(combat_log))

    assert loaded_log.events == combat_log.events
    assert isinstance(loaded_log.events[1], UnitWaitedEvent)
    assert isinstance(loaded_log.events[2], UnitSkippedEvent)


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
        executed_battle.move_stack("attacker-esquire", HexCoord(2, 5)),
    )

    replayed = replay_combat_log(initial_battle, combat_log)

    assert replayed.occupancy.unit_at(HexCoord(0, 5)) is None
    assert replayed.occupancy.unit_at(HexCoord(2, 5)) == "attacker-esquire"
    assert replayed.occupancy.unit_at(HexCoord(12, 5)) == "defender-esquire"


def test_replay_combat_log_reconstructs_attack_damage_state():
    catalog = load_packaged_unit_catalog()
    initial_battle = load_battle_initial_state_yaml(ADJACENT_INITIAL_STATE_YAML, catalog)
    executed_battle = load_battle_initial_state_yaml(ADJACENT_INITIAL_STATE_YAML, catalog)
    combat_log = CombatLog()
    combat_log.record_unit_attacked(
        TurnMarker(round_number=1, turn_number=1),
        executed_battle.attack_stack("attacker-esquire", "defender-esquire", damage_chooser=lambda damage: damage.minimum),
    )

    replayed = replay_combat_log(initial_battle, combat_log)

    assert replayed.stack("defender-esquire").count == executed_battle.stack("defender-esquire").count
    assert replayed.stack("defender-esquire").wound_damage == executed_battle.stack("defender-esquire").wound_damage
    assert replayed.stack("attacker-esquire").count == executed_battle.stack("attacker-esquire").count
    assert replayed.stack("attacker-esquire").wound_damage == executed_battle.stack("attacker-esquire").wound_damage


def test_replay_combat_log_accepts_wait_and_skip_events_without_mutating_battle():
    catalog = load_packaged_unit_catalog()
    initial_battle = load_battle_initial_state_yaml(VALID_INITIAL_STATE_YAML, catalog)
    combat_log = CombatLog()
    combat_log.record_unit_waited(TurnMarker(round_number=1, turn_number=1), "attacker-esquire")
    combat_log.record_unit_skipped(TurnMarker(round_number=1, turn_number=3), "attacker-esquire")

    replayed = replay_combat_log(initial_battle, combat_log)

    assert replayed.unit_stacks == initial_battle.unit_stacks
    assert replayed.occupancy.coordinate_for("attacker-esquire") == HexCoord(0, 5)


def test_apply_combat_log_event_mutates_battle_using_shared_replay_state():
    catalog = load_packaged_unit_catalog()
    battle = load_battle_initial_state_yaml(ADJACENT_INITIAL_STATE_YAML, catalog)
    executed_battle = load_battle_initial_state_yaml(ADJACENT_INITIAL_STATE_YAML, catalog)
    combat_log = CombatLog()
    event = combat_log.record_unit_attacked(
        TurnMarker(round_number=1, turn_number=1),
        executed_battle.attack_stack("attacker-esquire", "defender-esquire", damage_chooser=lambda damage: damage.minimum),
    )
    replay_state = CombatLogReplayState()

    apply_combat_log_event(battle, event, replay_state)

    assert battle.unit_stacks == executed_battle.unit_stacks
    assert replay_state.counterattacked_stack_ids_by_round == {(1, "defender-esquire")}


def test_replay_combat_log_rejects_movement_that_does_not_match_logged_path():
    catalog = load_packaged_unit_catalog()
    initial_battle = load_battle_initial_state_yaml(VALID_INITIAL_STATE_YAML, catalog)
    combat_log = CombatLog(
        events=(
            UnitMovedEvent(
                sequence=1,
                turn=TurnMarker(round_number=1, turn_number=1),
                stack_id="attacker-esquire",
                start=HexCoord(0, 5),
                destination=HexCoord(2, 5),
                path=(HexCoord(0, 5), HexCoord(2, 5)),
            ),
        )
    )

    with pytest.raises(CombatLogValidationError, match="movement"):
        replay_combat_log(initial_battle, combat_log)


def test_replay_combat_log_rejects_attack_that_does_not_match_logged_damage():
    catalog = load_packaged_unit_catalog()
    initial_battle = load_battle_initial_state_yaml(ADJACENT_INITIAL_STATE_YAML, catalog)
    executed_battle = load_battle_initial_state_yaml(ADJACENT_INITIAL_STATE_YAML, catalog)
    combat_log = CombatLog()
    event = combat_log.record_unit_attacked(
        TurnMarker(round_number=1, turn_number=1),
        executed_battle.attack_stack("attacker-esquire", "defender-esquire", damage_chooser=lambda damage: damage.minimum),
    )
    combat_log = CombatLog(
        events=(
            UnitAttackedEvent(
                sequence=event.sequence,
                turn=event.turn,
                attacker_id=event.attacker_id,
                defender_id=event.defender_id,
                primary_damage=event.primary_damage,
                counterattack=None,
            ),
        )
    )

    with pytest.raises(CombatLogValidationError, match="attack"):
        replay_combat_log(initial_battle, combat_log)
