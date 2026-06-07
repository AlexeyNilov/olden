from olden.combat.battle import Battle
from olden.combat.battlefield import Battlefield
from olden.combat.combat_log import UnitAttackedEvent, UnitMovedEvent, replay_combat_log
from olden.combat.combat_simulation import CombatSimulationStopReason, simulate_combat
from olden.combat.coordinates import HexCoord
from olden.combat.obstacles import Obstacle
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.units import AttackCategory, DamageRange, UnitCombatStats, UnitDefinition, UnitFootprint, UnitStack


def test_combat_simulation_moves_until_adjacent_then_logs_melee_attacks():
    initial_battle = _battle(
        player_stack=_stack("player-esquire", CombatSide.PLAYER, count=10),
        enemy_stack=_stack("enemy-esquire", CombatSide.ENEMY, count=20),
        player_anchor=HexCoord(0, 9),
        enemy_anchor=HexCoord(12, 5),
    )

    result = simulate_combat(
        initial_battle,
        first_stack_id="player-esquire",
        second_stack_id="enemy-esquire",
        path_chooser=lambda paths: paths[0],
        damage_chooser=lambda damage: damage.minimum,
    )

    movement_events = [event for event in result.combat_log.events if isinstance(event, UnitMovedEvent)]
    attack_events = [event for event in result.combat_log.events if isinstance(event, UnitAttackedEvent)]
    assert result.stop_reason is CombatSimulationStopReason.STACK_DEFEATED
    assert movement_events
    assert attack_events
    assert movement_events[-1].sequence < attack_events[0].sequence
    assert attack_events[0].attacker_id == movement_events[-1].stack_id
    assert "player-esquire" not in result.battle.unit_stacks or "enemy-esquire" not in result.battle.unit_stacks


def test_combat_simulation_attacks_after_moving_into_reach_in_same_turn():
    initial_battle = _battle(
        player_stack=_stack("player-esquire", CombatSide.PLAYER, count=10, speed=4),
        enemy_stack=_stack("enemy-esquire", CombatSide.ENEMY, count=20),
        player_anchor=HexCoord(0, 5),
        enemy_anchor=HexCoord(5, 5),
    )

    result = simulate_combat(
        initial_battle,
        first_stack_id="player-esquire",
        second_stack_id="enemy-esquire",
        path_chooser=lambda paths: next(path for path in paths if path[-1] == HexCoord(4, 5)),
        damage_chooser=lambda damage: damage.minimum,
        max_turns=1,
    )

    movement_events = [event for event in result.combat_log.events if isinstance(event, UnitMovedEvent)]
    attack_events = [event for event in result.combat_log.events if isinstance(event, UnitAttackedEvent)]
    assert result.stop_reason is CombatSimulationStopReason.MAX_TURNS_REACHED
    assert result.turns_taken == 1
    assert len(movement_events) == 1
    assert len(attack_events) == 1
    assert movement_events[0].sequence < attack_events[0].sequence
    assert movement_events[0].turn == attack_events[0].turn
    assert movement_events[0].destination == HexCoord(4, 5)
    assert attack_events[0].attacker_id == "player-esquire"
    assert attack_events[0].defender_id == "enemy-esquire"
    assert replay_combat_log(initial_battle, result.combat_log).unit_stacks == result.battle.unit_stacks


def test_combat_simulation_uses_initiative_order_with_multiple_stacks():
    player_esquire = _stack("player-esquire", CombatSide.PLAYER, count=10, initiative=5, speed=4)
    player_griffin = _stack("player-griffin", CombatSide.PLAYER, count=5, initiative=9, speed=5)
    enemy_esquire = _stack("enemy-esquire", CombatSide.ENEMY, count=20, initiative=5, speed=4)
    initial_battle = _battle_with_stacks(
        placements=(
            (player_esquire, HexCoord(0, 9)),
            (player_griffin, HexCoord(11, 5)),
            (enemy_esquire, HexCoord(12, 5)),
        )
    )

    result = simulate_combat(
        initial_battle,
        stack_ids=("player-esquire", "player-griffin", "enemy-esquire"),
        path_chooser=lambda paths: paths[0],
        damage_chooser=lambda damage: damage.minimum,
        max_turns=1,
    )

    attack_events = [event for event in result.combat_log.events if isinstance(event, UnitAttackedEvent)]
    assert result.stop_reason is CombatSimulationStopReason.MAX_TURNS_REACHED
    assert result.turns_taken == 1
    assert len(attack_events) == 1
    assert attack_events[0].attacker_id == "player-griffin"
    assert attack_events[0].defender_id == "enemy-esquire"
    assert attack_events[0].turn.round_number == 1
    assert attack_events[0].turn.turn_number == 1


def test_combat_simulation_targets_nearest_living_enemy_with_configured_order_tie_break():
    player = _stack("player-esquire", CombatSide.PLAYER, count=10, initiative=9, speed=4)
    enemy_first = _stack("enemy-first", CombatSide.ENEMY, count=20, initiative=5, speed=4)
    enemy_second = _stack("enemy-second", CombatSide.ENEMY, count=20, initiative=5, speed=4)
    initial_battle = _battle_with_stacks(
        placements=(
            (player, HexCoord(4, 5)),
            (enemy_first, HexCoord(5, 5)),
            (enemy_second, HexCoord(4, 4)),
        )
    )

    result = simulate_combat(
        initial_battle,
        stack_ids=("player-esquire", "enemy-first", "enemy-second"),
        damage_chooser=lambda damage: damage.minimum,
        max_turns=1,
    )

    attack_events = [event for event in result.combat_log.events if isinstance(event, UnitAttackedEvent)]
    assert len(attack_events) == 1
    assert attack_events[0].defender_id == "enemy-first"


def test_combat_simulation_allows_each_stack_to_counterattack_once_per_round():
    player_griffin = _stack("player-griffin", CombatSide.PLAYER, count=5, initiative=9, speed=5)
    player_esquire = _stack("player-esquire", CombatSide.PLAYER, count=10, initiative=5, speed=4)
    enemy_esquire = _stack("enemy-esquire", CombatSide.ENEMY, count=20, initiative=1, speed=4)
    initial_battle = _battle_with_stacks(
        placements=(
            (player_griffin, HexCoord(4, 5)),
            (player_esquire, HexCoord(5, 4)),
            (enemy_esquire, HexCoord(5, 5)),
        )
    )

    result = simulate_combat(
        initial_battle,
        stack_ids=("player-griffin", "player-esquire", "enemy-esquire"),
        damage_chooser=lambda damage: damage.minimum,
        max_turns=2,
    )

    attack_events = [event for event in result.combat_log.events if isinstance(event, UnitAttackedEvent)]
    assert len(attack_events) == 2
    assert attack_events[0].attacker_id == "player-griffin"
    assert attack_events[0].defender_id == "enemy-esquire"
    assert attack_events[0].counterattack is not None
    assert attack_events[1].attacker_id == "player-esquire"
    assert attack_events[1].defender_id == "enemy-esquire"
    assert attack_events[1].counterattack is None
    assert replay_combat_log(initial_battle, result.combat_log).unit_stacks == result.battle.unit_stacks


def test_combat_simulation_stops_after_first_attack_when_defender_is_defeated():
    initial_battle = _battle(
        player_stack=_stack("player-esquire", CombatSide.PLAYER, count=10),
        enemy_stack=_stack("enemy-esquire", CombatSide.ENEMY, count=1),
        player_anchor=HexCoord(0, 0),
        enemy_anchor=HexCoord(1, 0),
    )

    result = simulate_combat(
        initial_battle,
        first_stack_id="player-esquire",
        second_stack_id="enemy-esquire",
        damage_chooser=lambda damage: damage.minimum,
    )

    attack_events = [event for event in result.combat_log.events if isinstance(event, UnitAttackedEvent)]
    assert result.stop_reason is CombatSimulationStopReason.STACK_DEFEATED
    assert result.turns_taken == 1
    assert len(attack_events) == 1
    assert "enemy-esquire" not in result.battle.unit_stacks


def test_combat_simulation_does_not_mutate_initial_battle_and_log_replays_to_final_state():
    initial_battle = _battle(
        player_stack=_stack("player-esquire", CombatSide.PLAYER, count=10),
        enemy_stack=_stack("enemy-esquire", CombatSide.ENEMY, count=1),
        player_anchor=HexCoord(0, 0),
        enemy_anchor=HexCoord(1, 0),
    )

    result = simulate_combat(
        initial_battle,
        first_stack_id="player-esquire",
        second_stack_id="enemy-esquire",
        damage_chooser=lambda damage: damage.minimum,
    )
    replayed = replay_combat_log(initial_battle, result.combat_log)

    assert "enemy-esquire" in initial_battle.unit_stacks
    assert "enemy-esquire" not in replayed.unit_stacks
    assert replayed.unit_stacks == result.battle.unit_stacks
    assert replayed.occupancy.unit_at(HexCoord(1, 0)) is None


def test_combat_simulation_stops_when_no_engagement_path_is_reachable():
    initial_battle = _battle(
        player_stack=_stack("player-esquire", CombatSide.PLAYER, count=10),
        enemy_stack=_stack("enemy-esquire", CombatSide.ENEMY, count=20),
        player_anchor=HexCoord(0, 0),
        enemy_anchor=HexCoord(6, 5),
        obstacles=(
            HexCoord(5, 5),
            HexCoord(7, 5),
            HexCoord(5, 4),
            HexCoord(6, 4),
            HexCoord(5, 6),
            HexCoord(6, 6),
        ),
    )

    result = simulate_combat(
        initial_battle,
        first_stack_id="player-esquire",
        second_stack_id="enemy-esquire",
        damage_chooser=lambda damage: damage.minimum,
    )

    assert result.stop_reason is CombatSimulationStopReason.NO_REACHABLE_ENGAGEMENT
    assert result.turns_taken == 0


def _battle(
    player_stack: UnitStack,
    enemy_stack: UnitStack,
    player_anchor: HexCoord,
    enemy_anchor: HexCoord,
    obstacles: tuple[HexCoord, ...] = (),
) -> Battle:
    battlefield = Battlefield.default(
        obstacles=tuple(
            Obstacle(name=f"obstacle-{index}", coordinates=frozenset({coord})) for index, coord in enumerate(obstacles)
        )
    )
    occupancy = Occupancy(blocked_coordinates=battlefield.blocked_coordinates)
    occupancy.place(player_stack.id, player_anchor)
    occupancy.place(enemy_stack.id, enemy_anchor)
    return Battle(
        battlefield=battlefield,
        occupancy=occupancy,
        unit_stacks={player_stack.id: player_stack, enemy_stack.id: enemy_stack},
    )


def _battle_with_stacks(
    placements: tuple[tuple[UnitStack, HexCoord], ...],
    obstacles: tuple[HexCoord, ...] = (),
) -> Battle:
    battlefield = Battlefield.default(
        obstacles=tuple(
            Obstacle(name=f"obstacle-{index}", coordinates=frozenset({coord})) for index, coord in enumerate(obstacles)
        )
    )
    occupancy = Occupancy(blocked_coordinates=battlefield.blocked_coordinates)
    for stack, anchor in placements:
        occupancy.place(stack.id, anchor)
    return Battle(
        battlefield=battlefield,
        occupancy=occupancy,
        unit_stacks={stack.id: stack for stack, _anchor in placements},
    )


def _stack(
    stack_id: str,
    side: CombatSide,
    count: int,
    initiative: int = 5,
    speed: int = 4,
) -> UnitStack:
    return UnitStack(
        id=stack_id,
        definition=UnitDefinition(
            id="esquire",
            name="Swordsman",
            initiative=initiative,
            speed=speed,
            footprint=UnitFootprint.single_hex(),
            combat=UnitCombatStats(
                health=12,
                attack=4,
                defense=4,
                damage=DamageRange(minimum=2, maximum=3),
                attack_category=AttackCategory.MELEE,
            ),
        ),
        side=side,
        count=count,
    )
