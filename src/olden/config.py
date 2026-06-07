"""Configuration helpers"""

import logging
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from olden.exceptions import ConfigError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_BATTLE_INITIAL_STATE_PATH = PROJECT_ROOT / "data" / "demo_battle.yaml"
DEMO_COMBAT_LOG_PATH = PROJECT_ROOT / "data" / "demo_combat_log.yaml"
DEFAULT_GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE = 24
DEFAULT_GENETIC_STRATEGY_DISCOVERY_GENERATIONS = 20

SUPPORTED_LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def load_environment(
    dotenv_path: str | None = None,
    override: bool = False,
) -> bool:
    """Load environment variables from a dotenv file.

    Args:
        dotenv_path: Optional path to the dotenv file.
        override: Whether values from the file should override existing env vars.

    Returns:
        True if the dotenv file was loaded successfully, otherwise False.
    """
    resolved_path = dotenv_path or find_dotenv(usecwd=True)
    return load_dotenv(dotenv_path=resolved_path, override=override)


class Config:
    """Configuration sourced from environment variables."""

    def __init__(self):
        """Read settings from the current process environment."""

        self.log_level = self.get_log_level("LOG_LEVEL", default=logging.ERROR)
        self.replay_battle_initial_state_path = self.get_path_env(
            "REPLAY_BATTLE_INITIAL_STATE_PATH",
            default=DEMO_BATTLE_INITIAL_STATE_PATH,
        )
        self.replay_combat_log_path = self.get_path_env(
            "REPLAY_COMBAT_LOG_PATH",
            default=DEMO_COMBAT_LOG_PATH,
        )
        self.genetic_strategy_discovery_population_size = self.get_positive_int_env(
            "GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE",
            default=DEFAULT_GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE,
        )
        self.genetic_strategy_discovery_generations = self.get_positive_int_env(
            "GENETIC_STRATEGY_DISCOVERY_GENERATIONS",
            default=DEFAULT_GENETIC_STRATEGY_DISCOVERY_GENERATIONS,
        )

    def get_required_env(self, key: str) -> str:
        value = os.getenv(key)
        if not value or not value.strip():
            raise ConfigError(f"'{key}' is not set or empty")
        return value.strip()

    def get_log_level(self, key: str, default: int) -> int:
        value = os.getenv(key)
        if not value or not value.strip():
            return default

        normalized = value.strip().upper()
        if normalized not in SUPPORTED_LOG_LEVELS:
            supported = ", ".join(SUPPORTED_LOG_LEVELS)
            raise ConfigError(f"Unsupported {key} {value!r}; expected one of: {supported}")

        return SUPPORTED_LOG_LEVELS[normalized]

    def get_path_env(self, key: str, *, default: Path) -> Path:
        value = os.getenv(key)
        if not value or not value.strip():
            return default
        return Path(value.strip()).expanduser()

    def get_positive_int_env(self, key: str, *, default: int) -> int:
        value = os.getenv(key)
        if not value or not value.strip():
            return default
        try:
            parsed = int(value.strip())
        except ValueError as exc:
            raise ConfigError(f"{key} must be a positive integer") from exc
        if parsed < 1:
            raise ConfigError(f"{key} must be a positive integer")
        return parsed


def load_config() -> Config:
    load_environment()
    return Config()
