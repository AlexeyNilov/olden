from olden.combat.combat_simulation import CombatSimulationStopReason
from olden.strategy_discovery.stack_split import (
    StackSplitDiscoveryResult,
    StackSplitEvaluation,
    StackSplitFitness,
    StackSplitIndividual,
    StackSplitScenario,
)
from sample import genetic_strategy_discovery
from sample.genetic_strategy_discovery import run_genetic_strategy_discovery


def test_genetic_strategy_discovery_uses_configured_default_population_size(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE", raising=False)
    monkeypatch.delenv("GENETIC_STRATEGY_DISCOVERY_GENERATIONS", raising=False)
    monkeypatch.delenv("GENETIC_STRATEGY_DISCOVERY_MAX_TURNS", raising=False)
    monkeypatch.delenv("GENETIC_STRATEGY_DISCOVERY_MUTATION_RATE", raising=False)
    monkeypatch.delenv("GENETIC_STRATEGY_DISCOVERY_WORKERS", raising=False)
    tmp_path.joinpath(".env").write_text(
        "GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE=5\n"
        "GENETIC_STRATEGY_DISCOVERY_GENERATIONS=1\n"
        "GENETIC_STRATEGY_DISCOVERY_MAX_TURNS=1\n"
        "GENETIC_STRATEGY_DISCOVERY_MUTATION_RATE=0.5\n"
        "GENETIC_STRATEGY_DISCOVERY_WORKERS=1\n",
        encoding="utf-8",
    )

    result = run_genetic_strategy_discovery(
        best_battle_path=tmp_path / "genetic_best_battle.yaml",
        best_combat_log_path=tmp_path / "genetic_best_combat_log.yaml",
        seed=3,
    )

    assert len(result.discovery_result.population) == 5
    assert result.combat_result.turns_taken == 1
    assert result.combat_result.stop_reason is CombatSimulationStopReason.MAX_TURNS_REACHED


def test_genetic_strategy_discovery_passes_configured_mutation_rate(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GENETIC_STRATEGY_DISCOVERY_MUTATION_RATE", raising=False)
    tmp_path.joinpath(".env").write_text(
        "GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE=2\n"
        "GENETIC_STRATEGY_DISCOVERY_GENERATIONS=1\n"
        "GENETIC_STRATEGY_DISCOVERY_MAX_TURNS=1\n"
        "GENETIC_STRATEGY_DISCOVERY_MUTATION_RATE=0.75\n"
        "GENETIC_STRATEGY_DISCOVERY_WORKERS=1\n",
        encoding="utf-8",
    )
    captured: dict[str, float] = {}

    def discover_with_captured_mutation_rate(
        scenario: StackSplitScenario,
        *args: object,
        mutation_rate: float,
        **kwargs: object,
    ) -> StackSplitDiscoveryResult:
        captured["mutation_rate"] = mutation_rate
        genome = (scenario.unit_pool_size, 0, 0, 0, 0, 0, 0)
        individual = StackSplitIndividual(
            genome=genome,
            evaluation=StackSplitEvaluation(
                fitness=StackSplitFitness(
                    score=0,
                    player_surviving_units=0,
                    player_surviving_health=0,
                    enemy_units_killed=0,
                    turns_taken=0,
                ),
                stop_reason="test",
            ),
        )
        return StackSplitDiscoveryResult(best_individual=individual, population=(individual,))

    monkeypatch.setattr(genetic_strategy_discovery, "discover_stack_split_strategy", discover_with_captured_mutation_rate)

    run_genetic_strategy_discovery(
        best_battle_path=tmp_path / "genetic_best_battle.yaml",
        best_combat_log_path=tmp_path / "genetic_best_combat_log.yaml",
        seed=3,
    )

    assert captured["mutation_rate"] == 0.75
