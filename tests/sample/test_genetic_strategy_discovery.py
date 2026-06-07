from pathlib import Path

from olden.combat.combat_simulation import CombatSimulationStopReason
from olden.combat.targeting import TargetingPolicy
from olden.strategy_discovery.stack_split import (
    AttackerWaitPolicy,
    StackSplitDiscoveryResult,
    StackSplitEvaluation,
    StackSplitFitness,
    StackSplitIndividual,
    StackSplitScenario,
    StackSplitStrategy,
)
from sample import genetic_strategy_discovery
from sample.genetic_strategy_discovery import run_genetic_strategy_discovery

SAMPLE_INITIAL_STATE_YAML = """\
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
      row: 9
  - id: defender-esquire
    unit_id: esquire
    side: defender
    count: 20
    anchor:
      column: 12
      row: 5
"""


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
    initial_state_path = _write_sample_initial_state(tmp_path)

    result = run_genetic_strategy_discovery(
        initial_state_path=initial_state_path,
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
    initial_state_path = _write_sample_initial_state(tmp_path)
    captured: dict[str, float] = {}

    def discover_with_captured_mutation_rate(
        scenario: StackSplitScenario,
        *args: object,
        mutation_rate: float,
        **kwargs: object,
    ) -> StackSplitDiscoveryResult:
        captured["mutation_rate"] = mutation_rate
        strategy = StackSplitStrategy(
            stack_counts=(scenario.unit_pool_size, 0, 0, 0, 0, 0, 0),
            wait_policy=AttackerWaitPolicy.NEVER,
        )
        individual = StackSplitIndividual(
            strategy=strategy,
            evaluation=StackSplitEvaluation(
                fitness=StackSplitFitness(
                    score=0,
                    attacker_surviving_units=0,
                    attacker_surviving_health=0,
                    defender_units_killed=0,
                    turns_taken=0,
                ),
                stop_reason="test",
            ),
        )
        return StackSplitDiscoveryResult(best_individual=individual, population=(individual,))

    monkeypatch.setattr(genetic_strategy_discovery, "discover_stack_split_strategy", discover_with_captured_mutation_rate)

    run_genetic_strategy_discovery(
        initial_state_path=initial_state_path,
        best_battle_path=tmp_path / "genetic_best_battle.yaml",
        best_combat_log_path=tmp_path / "genetic_best_combat_log.yaml",
        seed=3,
    )

    assert captured["mutation_rate"] == 0.75


def test_genetic_strategy_discovery_passes_configured_targeting_policy(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("COMBAT_TARGETING_POLICY", raising=False)
    tmp_path.joinpath(".env").write_text(
        "COMBAT_TARGETING_POLICY=nearest_opponent\n"
        "GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE=2\n"
        "GENETIC_STRATEGY_DISCOVERY_GENERATIONS=1\n"
        "GENETIC_STRATEGY_DISCOVERY_MAX_TURNS=1\n"
        "GENETIC_STRATEGY_DISCOVERY_WORKERS=1\n",
        encoding="utf-8",
    )
    initial_state_path = _write_sample_initial_state(tmp_path)
    captured: dict[str, TargetingPolicy] = {}

    def discover_with_captured_targeting_policy(
        scenario: StackSplitScenario,
        *args: object,
        **kwargs: object,
    ) -> StackSplitDiscoveryResult:
        captured["targeting_policy"] = scenario.targeting_policy
        strategy = StackSplitStrategy(
            stack_counts=(scenario.unit_pool_size, 0, 0, 0, 0, 0, 0),
            wait_policy=AttackerWaitPolicy.NEVER,
        )
        individual = StackSplitIndividual(
            strategy=strategy,
            evaluation=StackSplitEvaluation(
                fitness=StackSplitFitness(
                    score=0,
                    attacker_surviving_units=0,
                    attacker_surviving_health=0,
                    defender_units_killed=0,
                    turns_taken=0,
                ),
                stop_reason="test",
            ),
        )
        return StackSplitDiscoveryResult(best_individual=individual, population=(individual,))

    monkeypatch.setattr(
        genetic_strategy_discovery,
        "discover_stack_split_strategy",
        discover_with_captured_targeting_policy,
    )

    run_genetic_strategy_discovery(
        initial_state_path=initial_state_path,
        best_battle_path=tmp_path / "genetic_best_battle.yaml",
        best_combat_log_path=tmp_path / "genetic_best_combat_log.yaml",
        seed=3,
    )

    assert captured["targeting_policy"] is TargetingPolicy.NEAREST_OPPONENT


def _write_sample_initial_state(tmp_path: Path) -> Path:
    initial_state_path = tmp_path / "genetic_battle.yaml"
    initial_state_path.write_text(SAMPLE_INITIAL_STATE_YAML, encoding="utf-8")
    return initial_state_path
