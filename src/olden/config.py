"""Configuration helpers"""

import logging
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from olden.exceptions import ConfigError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_BATTLE_INITIAL_STATE_PATH = PROJECT_ROOT / "data" / "demo_battle.yaml"
DEMO_COMBAT_LOG_PATH = PROJECT_ROOT / "data" / "demo_combat_log.yaml"

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


def load_config() -> Config:
    load_environment()
    return Config()
