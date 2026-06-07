from olden.combat.action_opportunities import CombatRoundState
from olden.combat.battle_setup import load_battle_initial_state_yaml
from olden.combat.combat_actions import apply_melee_attack_action, apply_movement_action, apply_skip_action, apply_wait_action
from olden.combat.combat_log import (
    CombatLog,
    TurnMarker,
    UnitAttackedEvent,
    UnitMovedEvent,
    UnitSkippedEvent,
    UnitWaitedEvent,
    replay_combat_log,
)
from olden.combat.coordinates import HexCoord
from olden.unit_data.packaged import load_packaged_unit_catalog

INITIAL_STATE_YAML = """
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
  - id: attacker-second
    unit_id: esquire
    side: attacker
    count: 10
    anchor:
      column: 1
      row: 4
  - id: defender-esquire
    unit_id: esquire
    side: defender
    count: 20
    anchor:
      column: 1
      row: 5
"""


def test_apply_movement_action_records_replayable_combat_log_event():
    catalog = load_packaged_unit_catalog()
    initial_battle = load_battle_initial_state_yaml(INITIAL_STATE_YAML, catalog)
    battle = initial_battle.copy()
    combat_log = CombatLog()

    event = apply_movement_action(
        battle,
        combat_log,
        TurnMarker(round_number=1, turn_number=1),
        "attacker-esquire",
        HexCoord(0, 6),
    )

    assert isinstance(event, UnitMovedEvent)
    assert event.stack_id == "attacker-esquire"
    assert event.start == HexCoord(0, 5)
    assert event.destination == HexCoord(0, 6)
    assert replay_combat_log(initial_battle, combat_log).unit_stacks == battle.unit_stacks


def test_apply_melee_attack_action_records_replayable_event_and_round_counterattack_state():
    catalog = load_packaged_unit_catalog()
    initial_battle = load_battle_initial_state_yaml(INITIAL_STATE_YAML, catalog)
    battle = initial_battle.copy()
    combat_log = CombatLog()
    round_state = CombatRoundState(round_number=1)

    first_event = apply_melee_attack_action(
        battle,
        combat_log,
        TurnMarker(round_number=1, turn_number=1),
        "attacker-esquire",
        "defender-esquire",
        damage_chooser=lambda damage: damage.minimum,
        round_state=round_state,
    )
    second_event = apply_melee_attack_action(
        battle,
        combat_log,
        TurnMarker(round_number=1, turn_number=2),
        "attacker-second",
        "defender-esquire",
        damage_chooser=lambda damage: damage.minimum,
        round_state=round_state,
    )

    assert isinstance(first_event, UnitAttackedEvent)
    assert first_event.counterattack is not None
    assert isinstance(second_event, UnitAttackedEvent)
    assert second_event.counterattack is None
    assert round_state.has_counterattacked("defender-esquire")
    assert replay_combat_log(initial_battle, combat_log).unit_stacks == battle.unit_stacks


def test_apply_wait_and_skip_actions_record_replayable_events():
    catalog = load_packaged_unit_catalog()
    initial_battle = load_battle_initial_state_yaml(INITIAL_STATE_YAML, catalog)
    battle = initial_battle.copy()
    combat_log = CombatLog()

    wait_event = apply_wait_action(
        combat_log,
        TurnMarker(round_number=1, turn_number=1),
        "attacker-esquire",
    )
    skip_event = apply_skip_action(
        combat_log,
        TurnMarker(round_number=1, turn_number=3),
        "attacker-esquire",
    )

    assert isinstance(wait_event, UnitWaitedEvent)
    assert wait_event.stack_id == "attacker-esquire"
    assert isinstance(skip_event, UnitSkippedEvent)
    assert skip_event.stack_id == "attacker-esquire"
    assert replay_combat_log(initial_battle, combat_log).unit_stacks == battle.unit_stacks
