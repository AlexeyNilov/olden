import pytest

from olden.combat.action_selection import CombatAction, CombatActionSelectionError
from olden.combat.battle import Battle
from olden.combat.battlefield import Battlefield
from olden.combat.combat_log import UnitAttackedEvent, UnitMovedEvent, UnitSkippedEvent, UnitWaitedEvent, replay_combat_log
from olden.combat.combat_simulation import CombatSimulationStopReason, simulate_combat
from olden.combat.coordinates import HexCoord
from olden.combat.obstacles import Obstacle
from olden.combat.occupancy import Occupancy
from olden.combat.range import distance_between
from olden.combat.sides import CombatSide
from olden.combat.targeting import TargetingPolicy
from olden.combat.units import AttackCategory, DamageRange, UnitCombatStats, UnitDefinition, UnitStack


def test_combat_simulation_moves_until_adjacent_then_logs_melee_attacks():
    initial_battle = _battle(
        attacker_stack=_stack("attacker-esquire", CombatSide.ATTACKER, count=10),
        defender_stack=_stack("defender-esquire", CombatSide.DEFENDER, count=20),
        attacker_anchor=HexCoord(0, 9),
        defender_anchor=HexCoord(12, 5),
    )

    result = simulate_combat(
        initial_battle,
        first_stack_id="attacker-esquire",
        second_stack_id="defender-esquire",
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
    assert "attacker-esquire" not in result.battle.unit_stacks or "defender-esquire" not in result.battle.unit_stacks


def test_combat_simulation_attacks_after_moving_into_reach_in_same_turn():
    initial_battle = _battle(
        attacker_stack=_stack("attacker-esquire", CombatSide.ATTACKER, count=10, speed=4),
        defender_stack=_stack("defender-esquire", CombatSide.DEFENDER, count=20),
        attacker_anchor=HexCoord(0, 5),
        defender_anchor=HexCoord(5, 5),
    )

    result = simulate_combat(
        initial_battle,
        first_stack_id="attacker-esquire",
        second_stack_id="defender-esquire",
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
    assert attack_events[0].attacker_id == "attacker-esquire"
    assert attack_events[0].defender_id == "defender-esquire"
    assert replay_combat_log(initial_battle, result.combat_log).unit_stacks == result.battle.unit_stacks


def test_combat_simulation_uses_initiative_order_with_multiple_stacks():
    attacker_esquire = _stack("attacker-esquire", CombatSide.ATTACKER, count=10, initiative=5, speed=4)
    attacker_griffin = _stack("attacker-griffin", CombatSide.ATTACKER, count=5, initiative=9, speed=5)
    defender_esquire = _stack("defender-esquire", CombatSide.DEFENDER, count=20, initiative=5, speed=4)
    initial_battle = _battle_with_stacks(
        placements=(
            (attacker_esquire, HexCoord(0, 9)),
            (attacker_griffin, HexCoord(11, 5)),
            (defender_esquire, HexCoord(12, 5)),
        )
    )

    result = simulate_combat(
        initial_battle,
        stack_ids=("attacker-esquire", "attacker-griffin", "defender-esquire"),
        path_chooser=lambda paths: paths[0],
        damage_chooser=lambda damage: damage.minimum,
        max_turns=1,
    )

    attack_events = [event for event in result.combat_log.events if isinstance(event, UnitAttackedEvent)]
    assert result.stop_reason is CombatSimulationStopReason.MAX_TURNS_REACHED
    assert result.turns_taken == 1
    assert len(attack_events) == 1
    assert attack_events[0].attacker_id == "attacker-griffin"
    assert attack_events[0].defender_id == "defender-esquire"
    assert attack_events[0].turn.round_number == 1
    assert attack_events[0].turn.turn_number == 1


def test_combat_simulation_targets_nearest_living_opponent_with_configured_order_tie_break():
    attacker = _stack("attacker-esquire", CombatSide.ATTACKER, count=10, initiative=9, speed=4)
    defender_first = _stack("defender-first", CombatSide.DEFENDER, count=20, initiative=5, speed=4)
    defender_second = _stack("defender-second", CombatSide.DEFENDER, count=20, initiative=5, speed=4)
    initial_battle = _battle_with_stacks(
        placements=(
            (attacker, HexCoord(4, 5)),
            (defender_first, HexCoord(5, 5)),
            (defender_second, HexCoord(4, 4)),
        )
    )

    result = simulate_combat(
        initial_battle,
        stack_ids=("attacker-esquire", "defender-first", "defender-second"),
        damage_chooser=lambda damage: damage.minimum,
        targeting_policy=TargetingPolicy.NEAREST_OPPONENT,
        max_turns=1,
    )

    attack_events = [event for event in result.combat_log.events if isinstance(event, UnitAttackedEvent)]
    assert len(attack_events) == 1
    assert attack_events[0].defender_id == "defender-first"


def test_combat_simulation_uses_threat_removed_targeting_by_default():
    attacker = _stack(
        "attacker-esquire",
        CombatSide.ATTACKER,
        count=10,
        initiative=9,
        speed=4,
        damage=DamageRange(minimum=4, maximum=4),
    )
    defender_near = _stack(
        "defender-near",
        CombatSide.DEFENDER,
        count=10,
        initiative=5,
        speed=4,
        damage=DamageRange(minimum=1, maximum=1),
    )
    defender_dangerous = _stack(
        "defender-dangerous",
        CombatSide.DEFENDER,
        count=1,
        initiative=5,
        speed=4,
        health=10,
        damage=DamageRange(minimum=10, maximum=10),
    )
    initial_battle = _battle_with_stacks(
        placements=(
            (attacker, HexCoord(4, 5)),
            (defender_near, HexCoord(5, 5)),
            (defender_dangerous, HexCoord(4, 4)),
        )
    )

    result = simulate_combat(
        initial_battle,
        stack_ids=("attacker-esquire", "defender-near", "defender-dangerous"),
        damage_chooser=lambda damage: damage.minimum,
        max_turns=1,
    )

    attack_events = [event for event in result.combat_log.events if isinstance(event, UnitAttackedEvent)]
    assert len(attack_events) == 1
    assert attack_events[0].defender_id == "defender-dangerous"


def test_combat_simulation_allows_each_stack_to_counterattack_once_per_round():
    attacker_griffin = _stack("attacker-griffin", CombatSide.ATTACKER, count=5, initiative=9, speed=5)
    attacker_esquire = _stack("attacker-esquire", CombatSide.ATTACKER, count=10, initiative=5, speed=4)
    defender_esquire = _stack("defender-esquire", CombatSide.DEFENDER, count=20, initiative=1, speed=4)
    initial_battle = _battle_with_stacks(
        placements=(
            (attacker_griffin, HexCoord(4, 5)),
            (attacker_esquire, HexCoord(5, 4)),
            (defender_esquire, HexCoord(5, 5)),
        )
    )

    result = simulate_combat(
        initial_battle,
        stack_ids=("attacker-griffin", "attacker-esquire", "defender-esquire"),
        damage_chooser=lambda damage: damage.minimum,
        max_turns=2,
    )

    attack_events = [event for event in result.combat_log.events if isinstance(event, UnitAttackedEvent)]
    assert len(attack_events) == 2
    assert attack_events[0].attacker_id == "attacker-griffin"
    assert attack_events[0].defender_id == "defender-esquire"
    assert attack_events[0].counterattack is not None
    assert attack_events[1].attacker_id == "attacker-esquire"
    assert attack_events[1].defender_id == "defender-esquire"
    assert attack_events[1].counterattack is None
    assert replay_combat_log(initial_battle, result.combat_log).unit_stacks == result.battle.unit_stacks


def test_combat_simulation_stops_after_first_attack_when_defender_is_defeated():
    initial_battle = _battle(
        attacker_stack=_stack("attacker-esquire", CombatSide.ATTACKER, count=10),
        defender_stack=_stack("defender-esquire", CombatSide.DEFENDER, count=1),
        attacker_anchor=HexCoord(0, 0),
        defender_anchor=HexCoord(1, 0),
    )

    result = simulate_combat(
        initial_battle,
        first_stack_id="attacker-esquire",
        second_stack_id="defender-esquire",
        damage_chooser=lambda damage: damage.minimum,
    )

    attack_events = [event for event in result.combat_log.events if isinstance(event, UnitAttackedEvent)]
    assert result.stop_reason is CombatSimulationStopReason.STACK_DEFEATED
    assert result.turns_taken == 1
    assert len(attack_events) == 1
    assert "defender-esquire" not in result.battle.unit_stacks


def test_combat_simulation_does_not_mutate_initial_battle_and_log_replays_to_final_state():
    initial_battle = _battle(
        attacker_stack=_stack("attacker-esquire", CombatSide.ATTACKER, count=10),
        defender_stack=_stack("defender-esquire", CombatSide.DEFENDER, count=1),
        attacker_anchor=HexCoord(0, 0),
        defender_anchor=HexCoord(1, 0),
    )

    result = simulate_combat(
        initial_battle,
        first_stack_id="attacker-esquire",
        second_stack_id="defender-esquire",
        damage_chooser=lambda damage: damage.minimum,
    )
    replayed = replay_combat_log(initial_battle, result.combat_log)

    assert "defender-esquire" in initial_battle.unit_stacks
    assert "defender-esquire" not in replayed.unit_stacks
    assert replayed.unit_stacks == result.battle.unit_stacks
    assert replayed.occupancy.unit_at(HexCoord(1, 0)) is None


def test_combat_simulation_stops_when_no_engagement_path_is_reachable():
    initial_battle = _battle(
        attacker_stack=_stack("attacker-esquire", CombatSide.ATTACKER, count=10),
        defender_stack=_stack("defender-esquire", CombatSide.DEFENDER, count=20),
        attacker_anchor=HexCoord(0, 0),
        defender_anchor=HexCoord(6, 5),
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
        first_stack_id="attacker-esquire",
        second_stack_id="defender-esquire",
        damage_chooser=lambda damage: damage.minimum,
    )

    assert result.stop_reason is CombatSimulationStopReason.NO_REACHABLE_ENGAGEMENT
    assert result.turns_taken == 0


def test_combat_simulation_wait_reschedules_without_counting_as_completed_turn():
    attacker = _stack("attacker-esquire", CombatSide.ATTACKER, count=10, initiative=9)
    defender = _stack("defender-esquire", CombatSide.DEFENDER, count=20, initiative=1)
    initial_battle = _battle_with_stacks(
        placements=((attacker, HexCoord(0, 0)), (defender, HexCoord(6, 0))),
    )

    result = simulate_combat(
        initial_battle,
        stack_ids=("attacker-esquire", "defender-esquire"),
        attacker_actions=(CombatAction.WAIT, CombatAction.SKIP),
        defender_actions=(CombatAction.SKIP,),
        action_chooser=lambda context: (
            CombatAction.WAIT if CombatAction.WAIT in context.applicable_actions else CombatAction.SKIP
        ),
        max_turns=1,
    )

    wait_events = [event for event in result.combat_log.events if isinstance(event, UnitWaitedEvent)]
    skip_events = [event for event in result.combat_log.events if isinstance(event, UnitSkippedEvent)]
    assert result.turns_taken == 1
    assert len(wait_events) == 1
    assert len(skip_events) == 1
    assert skip_events[0].stack_id == "defender-esquire"


def test_combat_simulation_wait_phase_uses_flipped_initiative_order_and_allows_one_wait_per_round():
    attacker_high = _stack("attacker-high", CombatSide.ATTACKER, count=10, initiative=9)
    attacker_low = _stack("attacker-low", CombatSide.ATTACKER, count=10, initiative=3)
    defender = _stack("defender-esquire", CombatSide.DEFENDER, count=20, initiative=1)
    initial_battle = _battle_with_stacks(
        placements=(
            (attacker_high, HexCoord(0, 0)),
            (attacker_low, HexCoord(0, 1)),
            (defender, HexCoord(6, 0)),
        ),
    )

    result = simulate_combat(
        initial_battle,
        stack_ids=("attacker-high", "attacker-low", "defender-esquire"),
        attacker_actions=(CombatAction.WAIT, CombatAction.SKIP),
        defender_actions=(CombatAction.SKIP,),
        action_chooser=lambda context: (
            CombatAction.WAIT if CombatAction.WAIT in context.applicable_actions else CombatAction.SKIP
        ),
        max_turns=3,
    )

    waited_stack_ids = [event.stack_id for event in result.combat_log.events if isinstance(event, UnitWaitedEvent)]
    skipped_stack_ids = [event.stack_id for event in result.combat_log.events if isinstance(event, UnitSkippedEvent)]
    assert waited_stack_ids == ["attacker-high", "attacker-low"]
    assert skipped_stack_ids == ["defender-esquire", "attacker-low", "attacker-high"]
    assert result.turns_taken == 3


def test_combat_simulation_raises_when_no_configured_action_is_applicable():
    initial_battle = _battle(
        attacker_stack=_stack("attacker-esquire", CombatSide.ATTACKER, count=10),
        defender_stack=_stack("defender-esquire", CombatSide.DEFENDER, count=20),
        attacker_anchor=HexCoord(0, 0),
        defender_anchor=HexCoord(6, 0),
    )

    with pytest.raises(CombatActionSelectionError, match="No configured combat action"):
        simulate_combat(
            initial_battle,
            first_stack_id="attacker-esquire",
            second_stack_id="defender-esquire",
            attacker_actions=(),
        )


def test_combat_simulation_can_move_to_stay_out_of_melee_reach_when_selected():
    initial_battle = _battle(
        attacker_stack=_stack("attacker-esquire", CombatSide.ATTACKER, count=10, speed=4),
        defender_stack=_stack("defender-esquire", CombatSide.DEFENDER, count=20, speed=4),
        attacker_anchor=HexCoord(0, 5),
        defender_anchor=HexCoord(8, 5),
    )

    result = simulate_combat(
        initial_battle,
        first_stack_id="attacker-esquire",
        second_stack_id="defender-esquire",
        attacker_actions=(CombatAction.STAY_OUT_OF_MELEE_REACH, CombatAction.MELEE_ENGAGE),
        defender_actions=(CombatAction.SKIP,),
        action_chooser=lambda context: (
            CombatAction.STAY_OUT_OF_MELEE_REACH
            if CombatAction.STAY_OUT_OF_MELEE_REACH in context.applicable_actions
            else context.applicable_actions[0]
        ),
        path_chooser=lambda paths: paths[0],
        max_turns=1,
    )

    movement_events = [event for event in result.combat_log.events if isinstance(event, UnitMovedEvent)]
    attack_events = [event for event in result.combat_log.events if isinstance(event, UnitAttackedEvent)]
    attacker_coord = result.battle.occupancy.coordinate_for("attacker-esquire")
    defender_coord = result.battle.occupancy.coordinate_for("defender-esquire")
    assert len(movement_events) == 1
    assert not attack_events
    assert attacker_coord is not None
    assert defender_coord is not None
    assert distance_between(result.battle.battlefield, attacker_coord, defender_coord) > 5


def _battle(
    attacker_stack: UnitStack,
    defender_stack: UnitStack,
    attacker_anchor: HexCoord,
    defender_anchor: HexCoord,
    obstacles: tuple[HexCoord, ...] = (),
) -> Battle:
    battlefield = Battlefield.default(
        obstacles=tuple(
            Obstacle(name=f"obstacle-{index}", coordinates=frozenset({coord})) for index, coord in enumerate(obstacles)
        )
    )
    occupancy = Occupancy(blocked_coordinates=battlefield.blocked_coordinates)
    occupancy.place(attacker_stack.id, attacker_anchor)
    occupancy.place(defender_stack.id, defender_anchor)
    return Battle(
        battlefield=battlefield,
        occupancy=occupancy,
        unit_stacks={attacker_stack.id: attacker_stack, defender_stack.id: defender_stack},
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
    health: int = 12,
    attack: int = 4,
    defense: int = 4,
    damage: DamageRange = DamageRange(minimum=2, maximum=3),
) -> UnitStack:
    return UnitStack(
        id=stack_id,
        definition=UnitDefinition(
            id="esquire",
            name="Swordsman",
            initiative=initiative,
            speed=speed,
            combat=UnitCombatStats(
                health=health,
                attack=attack,
                defense=defense,
                damage=damage,
                attack_category=AttackCategory.MELEE,
            ),
        ),
        side=side,
        count=count,
    )
