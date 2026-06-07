import random
from collections.abc import Callable
from pathlib import Path

from olden.combat.battle_setup import load_battle_initial_state_file
from olden.combat.combat_log import save_combat_log_file
from olden.combat.combat_simulation import CombatSimulationResult, MovementPath, simulate_combat
from olden.combat.units import DamageRange
from olden.unit_data.packaged import load_packaged_unit_catalog

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BATTLE_INITIAL_STATE_PATH = PROJECT_ROOT / "data" / "demo_battle.yaml"
DEFAULT_COMBAT_LOG_PATH = PROJECT_ROOT / "data" / "demo_combat_log.yaml"
ATTACKER_STACK_ID = "attacker-esquire"
ATTACKER_GRIFFIN_STACK_ID = "attacker-griffin"
DEFENDER_STACK_ID = "defender-esquire"


def run_demo_simulation(
    initial_state_path: Path = DEFAULT_BATTLE_INITIAL_STATE_PATH,
    combat_log_path: Path = DEFAULT_COMBAT_LOG_PATH,
    seed: int | None = None,
) -> CombatSimulationResult:
    battle = load_battle_initial_state_file(initial_state_path, load_packaged_unit_catalog())
    random_source = random.Random(seed)
    result = simulate_combat(
        initial_battle=battle,
        stack_ids=(ATTACKER_STACK_ID, ATTACKER_GRIFFIN_STACK_ID, DEFENDER_STACK_ID),
        path_chooser=_path_chooser(random_source),
        damage_chooser=_damage_chooser(random_source),
    )
    save_combat_log_file(combat_log_path, result.combat_log)
    return result


def main() -> None:
    run_demo_simulation()


def _path_chooser(random_source: random.Random) -> Callable[[tuple[MovementPath, ...]], MovementPath]:
    def choose_path(paths: tuple[MovementPath, ...]) -> MovementPath:
        return random_source.choice(paths)

    return choose_path


def _damage_chooser(random_source: random.Random) -> Callable[[DamageRange], int]:
    def choose_damage(damage: DamageRange) -> int:
        return random_source.randint(damage.minimum, damage.maximum)

    return choose_damage


if __name__ == "__main__":
    main()
