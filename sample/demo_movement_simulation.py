import random
from collections.abc import Callable
from pathlib import Path

from olden.combat.battle_setup import load_battle_initial_state_file
from olden.combat.combat_log import save_combat_log_file
from olden.combat.movement_simulation import MovementPath, MovementSimulationResult, simulate_movement_until_engaged
from olden.unit_data.packaged import load_packaged_unit_catalog

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BATTLE_INITIAL_STATE_PATH = PROJECT_ROOT / "data" / "demo_battle.yaml"
DEFAULT_COMBAT_LOG_PATH = PROJECT_ROOT / "data" / "demo_movement_log.yaml"
PLAYER_STACK_ID = "player-esquire"
ENEMY_STACK_ID = "enemy-esquire"


def run_demo_movement_simulation(
    initial_state_path: Path = DEFAULT_BATTLE_INITIAL_STATE_PATH,
    combat_log_path: Path = DEFAULT_COMBAT_LOG_PATH,
    seed: int | None = None,
) -> MovementSimulationResult:
    battle = load_battle_initial_state_file(initial_state_path, load_packaged_unit_catalog())
    result = simulate_movement_until_engaged(
        initial_battle=battle,
        first_stack_id=PLAYER_STACK_ID,
        second_stack_id=ENEMY_STACK_ID,
        path_chooser=_path_chooser(seed),
    )
    save_combat_log_file(combat_log_path, result.combat_log)
    return result


def main() -> None:
    run_demo_movement_simulation()


def _path_chooser(seed: int | None) -> Callable[[tuple[MovementPath, ...]], MovementPath]:
    random_source = random.Random(seed)

    def choose_path(paths: tuple[MovementPath, ...]) -> MovementPath:
        return random_source.choice(paths)

    return choose_path


if __name__ == "__main__":
    main()
