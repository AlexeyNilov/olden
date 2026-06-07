from olden.combat.battle import Battle
from olden.combat.battlefield import Battlefield
from olden.combat.combat_log import UnitMovedEvent, replay_combat_log
from olden.combat.coordinates import HexCoord
from olden.combat.movement_simulation import (
    MovementSimulationStopReason,
    simulate_movement_until_engaged,
)
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.units import AttackCategory, DamageRange, UnitCombatStats, UnitDefinition, UnitFootprint, UnitStack


def test_movement_simulation_moves_player_first_and_alternates_until_units_are_adjacent():
    initial_battle = _battle(
        player_anchor=HexCoord(0, 9),
        enemy_anchor=HexCoord(12, 5),
    )

    result = simulate_movement_until_engaged(
        initial_battle,
        first_stack_id="player-esquire",
        second_stack_id="enemy-esquire",
        path_chooser=lambda paths: paths[0],
    )

    movement_events = [event for event in result.combat_log.events if isinstance(event, UnitMovedEvent)]
    assert result.stop_reason is MovementSimulationStopReason.ENGAGED
    assert result.turns_taken == 4
    assert [event.stack_id for event in movement_events] == [
        "player-esquire",
        "enemy-esquire",
        "player-esquire",
        "enemy-esquire",
    ]
    assert movement_events[0].turn.round_number == 1
    assert movement_events[0].turn.turn_number == 1
    assert movement_events[1].turn.round_number == 1
    assert movement_events[1].turn.turn_number == 2
    assert movement_events[2].turn.round_number == 2
    assert movement_events[2].turn.turn_number == 1
    assert result.battle.occupancy.unit_at(HexCoord(7, 6)) == "enemy-esquire"
    assert HexCoord(7, 6) in result.battle.battlefield.neighbors(HexCoord(6, 6))


def test_movement_simulation_randomly_chooses_between_equally_short_engagement_paths():
    initial_battle = _battle(
        player_anchor=HexCoord(0, 0),
        enemy_anchor=HexCoord(2, 1),
    )
    seen_choices: list[tuple[tuple[HexCoord, ...], ...]] = []

    def choose_last(paths: tuple[tuple[HexCoord, ...], ...]) -> tuple[HexCoord, ...]:
        seen_choices.append(paths)
        return paths[-1]

    result = simulate_movement_until_engaged(
        initial_battle,
        first_stack_id="player-esquire",
        second_stack_id="enemy-esquire",
        path_chooser=choose_last,
    )

    assert len(seen_choices[0]) == 2
    assert result.battle.occupancy.unit_at(HexCoord(1, 0)) == "player-esquire"


def test_movement_simulation_does_not_mutate_initial_battle_and_log_replays_to_final_occupancy():
    initial_battle = _battle(
        player_anchor=HexCoord(0, 9),
        enemy_anchor=HexCoord(12, 5),
    )

    result = simulate_movement_until_engaged(
        initial_battle,
        first_stack_id="player-esquire",
        second_stack_id="enemy-esquire",
        path_chooser=lambda paths: paths[0],
    )
    replayed = replay_combat_log(initial_battle, result.combat_log)

    assert initial_battle.occupancy.unit_at(HexCoord(0, 9)) == "player-esquire"
    assert initial_battle.occupancy.unit_at(HexCoord(12, 5)) == "enemy-esquire"
    assert replayed.occupancy.unit_at(HexCoord(6, 6)) == result.battle.occupancy.unit_at(HexCoord(6, 6))
    assert replayed.occupancy.unit_at(HexCoord(7, 6)) == result.battle.occupancy.unit_at(HexCoord(7, 6))


def test_movement_simulation_stops_without_moving_when_units_start_adjacent():
    initial_battle = _battle(
        player_anchor=HexCoord(0, 0),
        enemy_anchor=HexCoord(1, 0),
    )

    result = simulate_movement_until_engaged(
        initial_battle,
        first_stack_id="player-esquire",
        second_stack_id="enemy-esquire",
    )

    assert result.stop_reason is MovementSimulationStopReason.ENGAGED
    assert result.turns_taken == 0
    assert len(result.combat_log.events) == 1


def _battle(player_anchor: HexCoord, enemy_anchor: HexCoord) -> Battle:
    battlefield = Battlefield.default()
    occupancy = Occupancy()
    stacks = {
        "player-esquire": _stack("player-esquire", CombatSide.PLAYER),
        "enemy-esquire": _stack("enemy-esquire", CombatSide.ENEMY),
    }
    occupancy.place("player-esquire", player_anchor)
    occupancy.place("enemy-esquire", enemy_anchor)
    return Battle(battlefield=battlefield, occupancy=occupancy, unit_stacks=stacks)


def _stack(stack_id: str, side: CombatSide) -> UnitStack:
    definition = UnitDefinition(
        id="esquire",
        name="Swordsman",
        speed=4,
        footprint=UnitFootprint.single_hex(),
        combat=UnitCombatStats(
            health=12,
            attack=4,
            defense=4,
            damage=DamageRange(minimum=2, maximum=3),
            attack_category=AttackCategory.MELEE,
        ),
    )
    return UnitStack(id=stack_id, definition=definition, side=side, count=10)
