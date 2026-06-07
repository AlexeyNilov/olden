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


def test_materialize_stack_split_battle_maps_non_empty_genome_slots_to_fixed_deployment_slots():
    scenario = _scenario()

    battle = materialize_stack_split_battle(scenario, (4, 0, 3, 1, 0, 2, 0))

    assert tuple(battle.unit_stacks) == (
        "genetic-player-1",
        "genetic-player-3",
        "genetic-player-4",
        "genetic-player-6",
        "enemy-esquire",
    )
    assert battle.stack("genetic-player-1").count == 4
    assert battle.stack("genetic-player-3").count == 3
    assert battle.stack("genetic-player-4").count == 1
    assert battle.stack("genetic-player-6").count == 2
    assert battle.occupancy.coordinates_for("genetic-player-1") == frozenset({HexCoord(0, 9)})
    assert battle.occupancy.coordinates_for("genetic-player-3") == frozenset({HexCoord(0, 7)})
    assert battle.occupancy.coordinates_for("genetic-player-4") == frozenset({HexCoord(0, 6)})
    assert battle.occupancy.coordinates_for("genetic-player-6") == frozenset({HexCoord(0, 4)})
    assert battle.occupancy.coordinates_for("enemy-esquire") == frozenset({HexCoord(12, 5)})


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
        player_pool_stack_id="player-esquire",
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
        generated_player_stack_id_prefix="genetic-player",
    )

    assert scenario.max_turns == 100


def test_evaluate_stack_split_uses_average_damage_for_repeatable_fitness():
    scenario = _scenario()

    first = evaluate_stack_split(scenario, (10, 0, 0, 0, 0, 0, 0))
    second = evaluate_stack_split(scenario, (10, 0, 0, 0, 0, 0, 0))

    assert first == second
    assert first.fitness.enemy_units_killed == 2
    assert first.fitness.player_surviving_units == 0
    assert first.fitness.score == 193


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
                player_surviving_units=0,
                player_surviving_health=0,
                enemy_units_killed=0,
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
        player_pool_stack_id="player-esquire",
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
        generated_player_stack_id_prefix="genetic-player",
        max_turns=100,
    )


def _base_battle() -> Battle:
    definition = load_packaged_unit_catalog().get("esquire").to_unit_definition()
    battlefield = Battlefield.default()
    occupancy = Occupancy(blocked_coordinates=battlefield.blocked_coordinates)
    player = UnitStack(id="player-esquire", definition=definition, side=CombatSide.PLAYER, count=10)
    enemy = UnitStack(id="enemy-esquire", definition=definition, side=CombatSide.ENEMY, count=20)
    occupancy.place(player.id, HexCoord(0, 9))
    occupancy.place(enemy.id, HexCoord(12, 5))
    return Battle(
        battlefield=battlefield,
        occupancy=occupancy,
        unit_stacks={player.id: player, enemy.id: enemy},
    )
