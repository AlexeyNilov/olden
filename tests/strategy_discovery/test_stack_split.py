import random

import pytest

from olden.combat.action_selection import CombatAction
from olden.combat.battle import Battle
from olden.combat.battlefield import Battlefield
from olden.combat.combat_log import UnitAttackedEvent, UnitWaitedEvent
from olden.combat.coordinates import HexCoord
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.units import DamageRange, UnitStack
from olden.strategy_discovery import stack_split
from olden.strategy_discovery.stack_split import (
    AttackerWaitPolicy,
    StackSplitEvaluation,
    StackSplitFitness,
    StackSplitScenario,
    StackSplitStrategy,
    average_damage,
    discover_stack_split_strategy,
    evaluate_stack_split,
    materialize_stack_split_battle,
    mutate_stack_split,
    simulate_stack_split,
    validate_stack_split,
)
from olden.unit_data.packaged import load_packaged_unit_catalog


def test_materialize_stack_split_battle_maps_non_empty_genome_slots_to_fixed_deployment_slots():
    scenario = _scenario()

    battle = materialize_stack_split_battle(
        scenario,
        StackSplitStrategy(stack_counts=(4, 0, 3, 1, 0, 2, 0), wait_policy=AttackerWaitPolicy.NEVER),
    )

    assert tuple(battle.unit_stacks) == (
        "genetic-attacker-1",
        "genetic-attacker-3",
        "genetic-attacker-4",
        "genetic-attacker-6",
        "defender-esquire",
    )
    assert battle.stack("genetic-attacker-1").count == 4
    assert battle.stack("genetic-attacker-3").count == 3
    assert battle.stack("genetic-attacker-4").count == 1
    assert battle.stack("genetic-attacker-6").count == 2
    assert battle.occupancy.coordinate_for("genetic-attacker-1") == HexCoord(0, 9)
    assert battle.occupancy.coordinate_for("genetic-attacker-3") == HexCoord(0, 7)
    assert battle.occupancy.coordinate_for("genetic-attacker-4") == HexCoord(0, 6)
    assert battle.occupancy.coordinate_for("genetic-attacker-6") == HexCoord(0, 4)
    assert battle.occupancy.coordinate_for("defender-esquire") == HexCoord(12, 5)


@pytest.mark.parametrize(
    "genome",
    [
        (10, 0, 0, 0, 0, 0, 0, 0),
        (9, 0, 0, 0, 0, 0, 0),
        (11, 0, 0, 0, 0, 0, 0),
        (9, -1, 0, 0, 0, 0, 2),
    ],
)
def test_validate_stack_split_rejects_genomes_outside_the_configured_unit_pool(genome):
    with pytest.raises(ValueError):
        validate_stack_split(genome, unit_pool_size=10, max_slots=7)


def test_stack_split_scenario_defaults_to_one_hundred_max_turns():
    scenario = StackSplitScenario(
        base_battle=_base_battle(),
        attacker_pool_stack_id="attacker-esquire",
        unit_pool_size=10,
        max_slots=7,
        deployment_slots=(
            HexCoord(0, 9),
            HexCoord(0, 8),
            HexCoord(0, 7),
            HexCoord(0, 6),
            HexCoord(0, 5),
            HexCoord(0, 4),
            HexCoord(0, 3),
        ),
        generated_attacker_stack_id_prefix="genetic-attacker",
    )

    assert scenario.max_turns == 100


def test_stack_split_scenario_rejects_deployment_slot_occupied_by_non_pool_stack():
    base_battle = _base_battle_with_attacker_support_stack()

    with pytest.raises(ValueError, match="Deployment slot is occupied"):
        StackSplitScenario(
            base_battle=base_battle,
            attacker_pool_stack_id="attacker-esquire",
            unit_pool_size=10,
            max_slots=2,
            deployment_slots=(HexCoord(0, 9), HexCoord(0, 5)),
            generated_attacker_stack_id_prefix="genetic-attacker",
        )


def test_evaluate_stack_split_uses_average_damage_for_repeatable_fitness():
    scenario = _scenario()
    strategy = StackSplitStrategy(stack_counts=(10, 0, 0, 0, 0, 0, 0), wait_policy=AttackerWaitPolicy.NEVER)

    first = evaluate_stack_split(scenario, strategy)
    second = evaluate_stack_split(scenario, strategy)

    assert first == second
    assert first.fitness.defender_units_killed == 2
    assert first.fitness.attacker_surviving_units == 0
    assert first.fitness.score == 268955


def test_evaluate_stack_split_prioritizes_defender_casualties_over_attacker_survival():
    scenario = _scenario(attacker_count=20)

    survival_first = evaluate_stack_split(
        scenario,
        StackSplitStrategy(stack_counts=(3, 9, 1, 4, 1, 1, 1), wait_policy=AttackerWaitPolicy.NEVER),
    )
    victory_progress_first = evaluate_stack_split(
        scenario,
        StackSplitStrategy(stack_counts=(1, 1, 0, 18, 0, 0, 0), wait_policy=AttackerWaitPolicy.NEVER),
    )

    assert survival_first.fitness.attacker_surviving_units > victory_progress_first.fitness.attacker_surviving_units
    assert survival_first.fitness.defender_units_killed < victory_progress_first.fitness.defender_units_killed
    assert survival_first.fitness.score < victory_progress_first.fitness.score


def test_mutate_stack_split_preserves_pool_size_and_slot_count():
    random_source = random.Random(7)
    strategy = StackSplitStrategy(stack_counts=(10, 0, 0, 0, 0, 0, 0), wait_policy=AttackerWaitPolicy.NEVER)

    mutated = mutate_stack_split(strategy, random_source)

    assert len(mutated.stack_counts) == 7
    assert sum(mutated.stack_counts) == 10
    assert mutated != strategy


def test_mutate_stack_split_can_change_wait_policy():
    random_source = random.Random(7)
    strategy = StackSplitStrategy(stack_counts=(10,), wait_policy=AttackerWaitPolicy.NEVER)

    mutated = mutate_stack_split(strategy, random_source, mutate_wait_policy=True)

    assert mutated.stack_counts == strategy.stack_counts
    assert mutated.wait_policy is AttackerWaitPolicy.FIRST_ACTION_IF_SAFE


def test_simulate_stack_split_first_action_if_safe_policy_records_attacker_wait():
    scenario = _scenario(max_turns=1)
    strategy = StackSplitStrategy(
        stack_counts=(10, 0, 0, 0, 0, 0, 0),
        wait_policy=AttackerWaitPolicy.FIRST_ACTION_IF_SAFE,
    )

    result = simulate_stack_split(scenario, strategy)

    wait_events = [event for event in result.combat_log.events if isinstance(event, UnitWaitedEvent)]
    assert len(wait_events) == 1
    assert wait_events[0].stack_id == "genetic-attacker-1"
    assert result.turns_taken == 1


def test_simulate_stack_split_prefers_ranged_attack_when_available_for_support_stack():
    scenario = StackSplitScenario(
        base_battle=_base_battle_with_attacker_support_stack(),
        attacker_pool_stack_id="attacker-esquire",
        unit_pool_size=10,
        max_slots=1,
        deployment_slots=(HexCoord(0, 9),),
        generated_attacker_stack_id_prefix="genetic-attacker",
        max_turns=3,
        attacker_actions=(CombatAction.RANGED_ATTACK, CombatAction.MELEE_ENGAGE),
        defender_actions=(CombatAction.MELEE_ENGAGE,),
    )
    strategy = StackSplitStrategy(stack_counts=(10,), wait_policy=AttackerWaitPolicy.NEVER)

    result = simulate_stack_split(scenario, strategy)

    attack_events = [event for event in result.combat_log.events if isinstance(event, UnitAttackedEvent)]
    assert len(attack_events) == 1
    assert attack_events[0].attacker_id == "attacker-crossbowman"
    assert attack_events[0].attack_kind == "ranged"


def test_discover_stack_split_strategy_returns_the_best_evaluated_individual():
    scenario = _scenario()

    result = discover_stack_split_strategy(
        scenario,
        random_source=random.Random(4),
        population_size=8,
        generations=3,
    )

    assert result.best_individual in result.population
    assert result.best_individual.evaluation == evaluate_stack_split(scenario, result.best_individual.strategy)
    assert all(sum(individual.strategy.stack_counts) == 10 for individual in result.population)


def test_discover_stack_split_strategy_reuses_repeated_genome_evaluations(monkeypatch):
    scenario = _scenario()
    strategy = StackSplitStrategy(stack_counts=(10, 0, 0, 0, 0, 0, 0), wait_policy=AttackerWaitPolicy.NEVER)
    evaluated_strategies: list[StackSplitStrategy] = []

    def evaluate_repeated_strategy(
        _scenario: StackSplitScenario, evaluated_strategy: StackSplitStrategy
    ) -> StackSplitEvaluation:
        evaluated_strategies.append(evaluated_strategy)
        return StackSplitEvaluation(
            fitness=StackSplitFitness(
                score=sum(evaluated_strategy.stack_counts),
                attacker_surviving_units=0,
                attacker_surviving_health=0,
                defender_units_killed=0,
                turns_taken=0,
            ),
            stop_reason="test",
        )

    monkeypatch.setattr(stack_split, "evaluate_stack_split", evaluate_repeated_strategy)
    monkeypatch.setattr(stack_split, "_initial_population_strategies", lambda *_args: (strategy, strategy, strategy, strategy))
    monkeypatch.setattr(stack_split, "_crossover_stack_split", lambda *_args: strategy)

    result = discover_stack_split_strategy(
        scenario,
        random_source=random.Random(4),
        population_size=4,
        generations=2,
        mutation_rate=0,
    )

    assert evaluated_strategies == [strategy]
    assert all(individual.evaluation == result.best_individual.evaluation for individual in result.population)


def test_discover_stack_split_strategy_parallel_evaluation_matches_serial_evaluation():
    scenario = _scenario()

    serial_result = discover_stack_split_strategy(
        scenario,
        random_source=random.Random(4),
        population_size=8,
        generations=2,
        worker_count=1,
    )
    parallel_result = discover_stack_split_strategy(
        scenario,
        random_source=random.Random(4),
        population_size=8,
        generations=2,
        worker_count=2,
    )

    assert parallel_result == serial_result


def test_average_damage_chooses_middle_value():
    assert average_damage(DamageRange(minimum=2, maximum=3)) == 2
    assert average_damage(DamageRange(minimum=1, maximum=5)) == 3


def _scenario(attacker_count: int = 10, defender_count: int = 20, max_turns: int = 100) -> StackSplitScenario:
    return StackSplitScenario(
        base_battle=_base_battle(attacker_count=attacker_count, defender_count=defender_count),
        attacker_pool_stack_id="attacker-esquire",
        unit_pool_size=attacker_count,
        max_slots=7,
        deployment_slots=(
            HexCoord(0, 9),
            HexCoord(0, 8),
            HexCoord(0, 7),
            HexCoord(0, 6),
            HexCoord(0, 5),
            HexCoord(0, 4),
            HexCoord(0, 3),
        ),
        generated_attacker_stack_id_prefix="genetic-attacker",
        max_turns=max_turns,
        attacker_actions=(CombatAction.MELEE_ENGAGE, CombatAction.WAIT),
    )


def _base_battle(attacker_count: int = 10, defender_count: int = 20) -> Battle:
    definition = load_packaged_unit_catalog().get("esquire").to_unit_definition()
    battlefield = Battlefield.default()
    occupancy = Occupancy(blocked_coordinates=battlefield.blocked_coordinates)
    attacker = UnitStack(id="attacker-esquire", definition=definition, side=CombatSide.ATTACKER, count=attacker_count)
    defender = UnitStack(id="defender-esquire", definition=definition, side=CombatSide.DEFENDER, count=defender_count)
    occupancy.place(attacker.id, HexCoord(0, 9))
    occupancy.place(defender.id, HexCoord(12, 5))
    return Battle(
        battlefield=battlefield,
        occupancy=occupancy,
        unit_stacks={attacker.id: attacker, defender.id: defender},
    )


def _base_battle_with_attacker_support_stack() -> Battle:
    catalog = load_packaged_unit_catalog()
    swordsman = catalog.get("esquire").to_unit_definition()
    crossbowman = catalog.get("crossbowman").to_unit_definition()
    battlefield = Battlefield.default()
    occupancy = Occupancy(blocked_coordinates=battlefield.blocked_coordinates)
    attacker = UnitStack(id="attacker-esquire", definition=swordsman, side=CombatSide.ATTACKER, count=10)
    support = UnitStack(id="attacker-crossbowman", definition=crossbowman, side=CombatSide.ATTACKER, count=5)
    defender = UnitStack(id="defender-esquire", definition=swordsman, side=CombatSide.DEFENDER, count=20)
    occupancy.place(attacker.id, HexCoord(0, 9))
    occupancy.place(support.id, HexCoord(0, 5))
    occupancy.place(defender.id, HexCoord(12, 5))
    return Battle(
        battlefield=battlefield,
        occupancy=occupancy,
        unit_stacks={attacker.id: attacker, support.id: support, defender.id: defender},
    )
