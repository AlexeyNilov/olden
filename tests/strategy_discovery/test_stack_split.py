import random

import pytest

from olden.combat.battle import Battle
from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.units import DamageRange, UnitStack
from olden.strategy_discovery import stack_split
from olden.strategy_discovery.stack_split import (
    StackSplitEvaluation,
    StackSplitFitness,
    StackSplitScenario,
    average_damage,
    discover_stack_split_strategy,
    evaluate_stack_split,
    materialize_stack_split_battle,
    mutate_stack_split,
    validate_stack_split,
)
from olden.unit_data.packaged import load_packaged_unit_catalog
from sample.genetic_strategy_discovery import ATTACKER_POOL_STACK_ID, DEFAULT_ATTACKER_DEPLOYMENT_SLOTS


def test_materialize_stack_split_battle_maps_non_empty_genome_slots_to_fixed_deployment_slots():
    scenario = _scenario()

    battle = materialize_stack_split_battle(scenario, (4, 0, 3, 1, 0, 2, 0))

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


def test_evaluate_stack_split_uses_average_damage_for_repeatable_fitness():
    scenario = _scenario()

    first = evaluate_stack_split(scenario, (10, 0, 0, 0, 0, 0, 0))
    second = evaluate_stack_split(scenario, (10, 0, 0, 0, 0, 0, 0))

    assert first == second
    assert first.fitness.defender_units_killed == 2
    assert first.fitness.attacker_surviving_units == 0
    assert first.fitness.score == 268955


def test_evaluate_stack_split_prioritizes_defender_casualties_over_attacker_survival():
    scenario = _genetic_sample_scenario()

    survival_first = evaluate_stack_split(scenario, (3, 9, 1, 4, 1, 1, 1))
    victory_progress_first = evaluate_stack_split(scenario, (1, 1, 0, 18, 0, 0, 0))

    assert survival_first.fitness.attacker_surviving_units > victory_progress_first.fitness.attacker_surviving_units
    assert survival_first.fitness.defender_units_killed < victory_progress_first.fitness.defender_units_killed
    assert survival_first.fitness.score < victory_progress_first.fitness.score


def test_mutate_stack_split_preserves_pool_size_and_slot_count():
    random_source = random.Random(7)

    mutated = mutate_stack_split((10, 0, 0, 0, 0, 0, 0), random_source)

    assert len(mutated) == 7
    assert sum(mutated) == 10
    assert mutated != (10, 0, 0, 0, 0, 0, 0)


def test_discover_stack_split_strategy_returns_the_best_evaluated_individual():
    scenario = _scenario()

    result = discover_stack_split_strategy(
        scenario,
        random_source=random.Random(4),
        population_size=8,
        generations=3,
    )

    assert result.best_individual in result.population
    assert result.best_individual.evaluation == evaluate_stack_split(scenario, result.best_individual.genome)
    assert all(sum(individual.genome) == 10 for individual in result.population)


def test_discover_stack_split_strategy_reuses_repeated_genome_evaluations(monkeypatch):
    scenario = _scenario()
    genome = (10, 0, 0, 0, 0, 0, 0)
    evaluated_genomes: list[tuple[int, ...]] = []

    def evaluate_repeated_genome(_scenario: StackSplitScenario, evaluated_genome: tuple[int, ...]) -> StackSplitEvaluation:
        evaluated_genomes.append(evaluated_genome)
        return StackSplitEvaluation(
            fitness=StackSplitFitness(
                score=sum(evaluated_genome),
                attacker_surviving_units=0,
                attacker_surviving_health=0,
                defender_units_killed=0,
                turns_taken=0,
            ),
            stop_reason="test",
        )

    monkeypatch.setattr(stack_split, "evaluate_stack_split", evaluate_repeated_genome)
    monkeypatch.setattr(stack_split, "_initial_population_genomes", lambda *_args: (genome, genome, genome, genome))
    monkeypatch.setattr(stack_split, "_crossover_stack_split", lambda *_args: genome)

    result = discover_stack_split_strategy(
        scenario,
        random_source=random.Random(4),
        population_size=4,
        generations=2,
        mutation_rate=0,
    )

    assert evaluated_genomes == [genome]
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


def _scenario() -> StackSplitScenario:
    return StackSplitScenario(
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
        max_turns=100,
    )


def _base_battle() -> Battle:
    definition = load_packaged_unit_catalog().get("esquire").to_unit_definition()
    battlefield = Battlefield.default()
    occupancy = Occupancy(blocked_coordinates=battlefield.blocked_coordinates)
    attacker = UnitStack(id="attacker-esquire", definition=definition, side=CombatSide.ATTACKER, count=10)
    defender = UnitStack(id="defender-esquire", definition=definition, side=CombatSide.DEFENDER, count=20)
    occupancy.place(attacker.id, HexCoord(0, 9))
    occupancy.place(defender.id, HexCoord(12, 5))
    return Battle(
        battlefield=battlefield,
        occupancy=occupancy,
        unit_stacks={attacker.id: attacker, defender.id: defender},
    )


def _genetic_sample_scenario() -> StackSplitScenario:
    from olden.combat.battle_setup import load_battle_initial_state_file
    from sample.genetic_strategy_discovery import DEFAULT_BATTLE_INITIAL_STATE_PATH

    battle = load_battle_initial_state_file(DEFAULT_BATTLE_INITIAL_STATE_PATH, load_packaged_unit_catalog())
    return StackSplitScenario(
        base_battle=battle,
        attacker_pool_stack_id=ATTACKER_POOL_STACK_ID,
        unit_pool_size=battle.stack(ATTACKER_POOL_STACK_ID).count,
        max_slots=len(DEFAULT_ATTACKER_DEPLOYMENT_SLOTS),
        deployment_slots=DEFAULT_ATTACKER_DEPLOYMENT_SLOTS,
        generated_attacker_stack_id_prefix="genetic-attacker",
        max_turns=100,
    )
