from olden.battlefield_view.model import build_battlefield_view, build_battlefield_view_for_battle
from olden.combat.battle_setup import load_battle_initial_state_yaml
from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.obstacles import Obstacle
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.units import AttackCategory, DamageRange, UnitCombatStats, UnitDefinition, UnitFootprint, UnitStack
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
"""


def test_battlefield_view_exposes_deployment_zone_state_for_each_renderable_hex():
    view = build_battlefield_view(Battlefield.default(), Occupancy())

    assert view.hex_at(HexCoord(0, 4)).deployment_side is CombatSide.PLAYER
    assert view.hex_at(HexCoord(5, 4)).deployment_side is None
    assert view.hex_at(HexCoord(11, 4)).deployment_side is CombatSide.ENEMY


def test_battlefield_view_exposes_blocked_state_for_obstacle_coordinates():
    obstacle = Obstacle(name="rocks", coordinates=frozenset({HexCoord(2, 3)}))
    battlefield = Battlefield.default(obstacles=(obstacle,))

    view = build_battlefield_view(battlefield, Occupancy(blocked_coordinates=obstacle.coordinates))

    assert view.hex_at(HexCoord(2, 3)).is_blocked
    assert not view.hex_at(HexCoord(3, 3)).is_blocked


def test_battlefield_view_exposes_occupying_unit_identity_and_optional_stack_metadata():
    swordsman = UnitStack(
        id="unit-1",
        definition=UnitDefinition(
            id="swordsman",
            name="Swordsman",
            speed=4,
            footprint=UnitFootprint.single_hex(),
            combat=_combat_stats(),
        ),
        side=CombatSide.PLAYER,
        count=12,
    )
    occupancy = Occupancy()
    occupancy.place(swordsman.id, HexCoord(4, 5))

    view = build_battlefield_view(Battlefield.default(), occupancy, unit_stacks={swordsman.id: swordsman})

    renderable_hex = view.hex_at(HexCoord(4, 5))
    assert renderable_hex.occupant_id == swordsman.id
    assert renderable_hex.unit_stack == swordsman


def test_battlefield_view_does_not_mutate_occupancy():
    occupancy = Occupancy()
    occupancy.place("unit-1", HexCoord(4, 5))

    build_battlefield_view(Battlefield.default(), occupancy)

    assert occupancy.unit_at(HexCoord(4, 5)) == "unit-1"


def test_battlefield_view_can_render_loaded_battle_state():
    battle = load_battle_initial_state_yaml(VALID_INITIAL_STATE_YAML, load_packaged_unit_catalog())

    view = build_battlefield_view_for_battle(battle)

    renderable_hex = view.hex_at(HexCoord(0, 5))
    assert renderable_hex.occupant_id == "player-esquire"
    assert renderable_hex.unit_stack == battle.unit_stacks["player-esquire"]


def _combat_stats() -> UnitCombatStats:
    return UnitCombatStats(
        health=12,
        attack=4,
        defense=4,
        damage=DamageRange(minimum=2, maximum=3),
        attack_category=AttackCategory.MELEE,
    )
