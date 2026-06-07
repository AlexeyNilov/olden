import pytest

from olden.combat.battle_setup import load_battle_initial_state_yaml
from olden.combat.combat_log import (
    CombatLog,
    CombatLogValidationError,
    TurnMarker,
    UnitAttackedEvent,
    UnitMovedEvent,
    replay_combat_log,
)
from olden.combat.combat_replay import build_combat_replay_frames
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


def test_combat_replay_frames_include_initial_frame_and_one_frame_per_movement_event():
    initial_battle = load_battle_initial_state_yaml(VALID_INITIAL_STATE_YAML, load_packaged_unit_catalog())
    combat_log = CombatLog()
    combat_log.record_battle_started()
    combat_log.record_unit_moved(
        TurnMarker(round_number=1, turn_number=1),
        initial_battle.copy().move_stack("attacker-esquire", HexCoord(2, 5)),
    )

    frames = build_combat_replay_frames(initial_battle, combat_log)

    assert len(frames) == 2
    assert frames[0].index == 0
    assert frames[0].total == 2
    assert frames[0].event is None
    assert frames[0].battle.occupancy.unit_at(HexCoord(0, 5)) == "attacker-esquire"
    assert frames[1].index == 1
    assert frames[1].total == 2
    assert isinstance(frames[1].event, UnitMovedEvent)
    assert frames[1].battle.occupancy.unit_at(HexCoord(2, 5)) == "attacker-esquire"


def test_combat_replay_final_frame_matches_full_combat_log_replay():
    initial_battle = load_battle_initial_state_yaml(VALID_INITIAL_STATE_YAML, load_packaged_unit_catalog())
    executed_battle = initial_battle.copy()
    combat_log = CombatLog()
    combat_log.record_unit_moved(
        TurnMarker(round_number=1, turn_number=1),
        executed_battle.move_stack("attacker-esquire", HexCoord(2, 5)),
    )
    combat_log.record_unit_moved(
        TurnMarker(round_number=1, turn_number=2),
        executed_battle.move_stack("defender-esquire", HexCoord(10, 5)),
    )

    frames = build_combat_replay_frames(initial_battle, combat_log)
    replayed = replay_combat_log(initial_battle, combat_log)

    assert frames[-1].battle.occupancy.unit_at(HexCoord(2, 5)) == replayed.occupancy.unit_at(HexCoord(2, 5))
    assert frames[-1].battle.occupancy.unit_at(HexCoord(10, 5)) == replayed.occupancy.unit_at(HexCoord(10, 5))


def test_combat_replay_frames_include_attack_events_and_updated_stack_state():
    initial_battle = load_battle_initial_state_yaml(ADJACENT_INITIAL_STATE_YAML, load_packaged_unit_catalog())
    executed_battle = initial_battle.copy()
    combat_log = CombatLog()
    combat_log.record_battle_started()
    combat_log.record_unit_attacked(
        TurnMarker(round_number=1, turn_number=1),
        executed_battle.attack_stack("attacker-esquire", "defender-esquire", damage_chooser=lambda damage: damage.minimum),
    )

    frames = build_combat_replay_frames(initial_battle, combat_log)

    assert len(frames) == 2
    assert isinstance(frames[1].event, UnitAttackedEvent)
    assert frames[1].battle.stack("defender-esquire").count == executed_battle.stack("defender-esquire").count
    assert frames[1].battle.stack("attacker-esquire").wound_damage == executed_battle.stack("attacker-esquire").wound_damage


def test_combat_replay_frames_reject_movement_events_that_do_not_replay():
    initial_battle = load_battle_initial_state_yaml(VALID_INITIAL_STATE_YAML, load_packaged_unit_catalog())
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
        build_combat_replay_frames(initial_battle, combat_log)


def test_combat_replay_frames_reject_attack_events_that_do_not_replay():
    initial_battle = load_battle_initial_state_yaml(ADJACENT_INITIAL_STATE_YAML, load_packaged_unit_catalog())
    executed_battle = initial_battle.copy()
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
        build_combat_replay_frames(initial_battle, combat_log)
