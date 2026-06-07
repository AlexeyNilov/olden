import random
from dataclasses import dataclass
from pathlib import Path

from olden.combat.battle_setup import load_battle_initial_state_file, save_battle_initial_state_file
from olden.combat.combat_log import save_combat_log_file
from olden.combat.combat_simulation import CombatSimulationResult
from olden.combat.coordinates import HexCoord
from olden.strategy_discovery.stack_split import (
    StackSplitDiscoveryResult,
    StackSplitScenario,
    discover_stack_split_strategy,
    materialize_stack_split_battle,
    simulate_stack_split,
)
from olden.unit_data.packaged import load_packaged_unit_catalog

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BATTLE_INITIAL_STATE_PATH = PROJECT_ROOT / "data" / "genetic_battle.yaml"
DEFAULT_BEST_BATTLE_PATH = PROJECT_ROOT / "data" / "genetic_best_battle.yaml"
DEFAULT_BEST_COMBAT_LOG_PATH = PROJECT_ROOT / "data" / "genetic_best_combat_log.yaml"
PLAYER_POOL_STACK_ID = "player-esquire"

DEFAULT_PLAYER_DEPLOYMENT_SLOTS = (
    HexCoord(0, 9),
    HexCoord(0, 8),
    HexCoord(0, 7),
    HexCoord(0, 6),
    HexCoord(0, 5),
    HexCoord(0, 4),
    HexCoord(0, 3),
)


@dataclass(frozen=True, slots=True)
class GeneticStrategyDiscoverySampleResult:
    discovery_result: StackSplitDiscoveryResult
    combat_result: CombatSimulationResult


def run_genetic_strategy_discovery(
    initial_state_path: Path = DEFAULT_BATTLE_INITIAL_STATE_PATH,
    best_battle_path: Path = DEFAULT_BEST_BATTLE_PATH,
    best_combat_log_path: Path = DEFAULT_BEST_COMBAT_LOG_PATH,
    seed: int | None = None,
    population_size: int = 100,
    generations: int = 20,
) -> GeneticStrategyDiscoverySampleResult:
    battle = load_battle_initial_state_file(initial_state_path, load_packaged_unit_catalog())
    scenario = StackSplitScenario(
        base_battle=battle,
        player_pool_stack_id=PLAYER_POOL_STACK_ID,
        unit_pool_size=battle.stack(PLAYER_POOL_STACK_ID).count,
        max_slots=len(DEFAULT_PLAYER_DEPLOYMENT_SLOTS),
        deployment_slots=DEFAULT_PLAYER_DEPLOYMENT_SLOTS,
        generated_player_stack_id_prefix="genetic-player",
    )
    discovery_result = discover_stack_split_strategy(
        scenario,
        random_source=random.Random(seed),
        population_size=population_size,
        generations=generations,
    )
    best_genome = discovery_result.best_individual.genome
    best_battle = materialize_stack_split_battle(scenario, best_genome)
    combat_result = simulate_stack_split(scenario, best_genome)
    save_battle_initial_state_file(best_battle_path, best_battle)
    save_combat_log_file(best_combat_log_path, combat_result.combat_log)
    return GeneticStrategyDiscoverySampleResult(discovery_result=discovery_result, combat_result=combat_result)


def main() -> None:
    result = run_genetic_strategy_discovery()
    best = result.discovery_result.best_individual
    fitness = best.evaluation.fitness
    print(f"Best genome: {best.genome}")
    print(f"Fitness: {fitness.score}")
    print(f"Player survivors: {fitness.player_surviving_units}")
    print(f"Enemy units killed: {fitness.enemy_units_killed}")
    print(f"Turns: {fitness.turns_taken}")
    print("Replay:")
    print(f"  battle: {DEFAULT_BEST_BATTLE_PATH}")
    print(f"  log: {DEFAULT_BEST_COMBAT_LOG_PATH}")


if __name__ == "__main__":
    main()
