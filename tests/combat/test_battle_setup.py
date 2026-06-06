import pytest

from olden.combat.battle import Battle
from olden.combat.battle_setup import (
    BattleSetupValidationError,
    dump_battle_initial_state_yaml,
    load_battle_initial_state_file,
    load_battle_initial_state_yaml,
    save_battle_initial_state_file,
)
from olden.combat.coordinates import HexCoord
from olden.combat.sides import CombatSide
from olden.unit_data.packaged import load_packaged_unit_catalog

VALID_INITIAL_STATE_YAML = """
schema_version: 1
battlefield:
  obstacles:
    - name: rocks
      coordinates:
        - column: 5
          row: 4
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


def test_load_battle_initial_state_builds_battle_with_units_and_obstacles():
    battle = load_battle_initial_state_yaml(VALID_INITIAL_STATE_YAML, load_packaged_unit_catalog())

    assert isinstance(battle, Battle)
    assert battle.battlefield.is_blocked(HexCoord(5, 4))
    assert battle.occupancy.unit_at(HexCoord(0, 5)) == "player-esquire"
    assert battle.occupancy.unit_at(HexCoord(12, 5)) == "enemy-esquire"
    assert battle.unit_stacks["player-esquire"].definition.id == "esquire"
    assert battle.unit_stacks["player-esquire"].side is CombatSide.PLAYER


def test_load_battle_initial_state_rejects_blocked_starting_units():
    blocked_state = VALID_INITIAL_STATE_YAML.replace("column: 0\n      row: 5", "column: 5\n      row: 4")

    with pytest.raises(BattleSetupValidationError, match="blocked"):
        load_battle_initial_state_yaml(blocked_state, load_packaged_unit_catalog())


def test_load_battle_initial_state_rejects_overlapping_starting_units():
    overlapping_state = VALID_INITIAL_STATE_YAML.replace("column: 12\n      row: 5", "column: 0\n      row: 5")

    with pytest.raises(BattleSetupValidationError, match="occupied"):
        load_battle_initial_state_yaml(overlapping_state, load_packaged_unit_catalog())


def test_save_battle_initial_state_round_trips_loaded_battle():
    catalog = load_packaged_unit_catalog()
    battle = load_battle_initial_state_yaml(VALID_INITIAL_STATE_YAML, catalog)

    dumped = dump_battle_initial_state_yaml(battle)
    loaded = load_battle_initial_state_yaml(dumped, catalog)

    assert loaded.battlefield.obstacles == battle.battlefield.obstacles
    assert loaded.unit_stacks == battle.unit_stacks
    assert loaded.occupancy.unit_at(HexCoord(0, 5)) == "player-esquire"
    assert loaded.occupancy.unit_at(HexCoord(12, 5)) == "enemy-esquire"


def test_save_battle_initial_state_file_writes_loadable_yaml(tmp_path):
    catalog = load_packaged_unit_catalog()
    battle = load_battle_initial_state_yaml(VALID_INITIAL_STATE_YAML, catalog)
    path = tmp_path / "battle.yaml"

    save_battle_initial_state_file(path, battle)
    loaded = load_battle_initial_state_file(path, catalog)

    assert loaded.unit_stacks == battle.unit_stacks
    assert loaded.occupancy.unit_at(HexCoord(0, 5)) == "player-esquire"
