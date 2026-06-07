import logging
from pathlib import Path

import pytest

from olden.config import (
    DEFAULT_GENETIC_STRATEGY_DISCOVERY_GENERATIONS,
    DEFAULT_GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE,
    DEFAULT_GENETIC_STRATEGY_DISCOVERY_WORKERS,
    DEMO_BATTLE_INITIAL_STATE_PATH,
    DEMO_COMBAT_LOG_PATH,
    load_config,
)


def test_load_config_reads_log_level_from_dotenv_file(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    tmp_path.joinpath(".env").write_text("LOG_LEVEL=debug\n", encoding="utf-8")

    config = load_config()

    assert config.log_level == logging.DEBUG


def test_load_config_prefers_existing_log_level_env_var(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LOG_LEVEL", "warning")
    tmp_path.joinpath(".env").write_text("LOG_LEVEL=ERROR\n", encoding="utf-8")

    config = load_config()

    assert config.log_level == logging.WARNING


def test_load_config_rejects_unknown_log_level(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    tmp_path.joinpath(".env").write_text("LOG_LEVEL=LOUD\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported LOG_LEVEL"):
        load_config()


def test_load_config_reads_replay_paths_from_dotenv_file(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("REPLAY_BATTLE_INITIAL_STATE_PATH", raising=False)
    monkeypatch.delenv("REPLAY_COMBAT_LOG_PATH", raising=False)
    tmp_path.joinpath(".env").write_text(
        "REPLAY_BATTLE_INITIAL_STATE_PATH=custom/battle.yaml\nREPLAY_COMBAT_LOG_PATH=custom/combat_log.yaml\n",
        encoding="utf-8",
    )

    config = load_config()

    assert config.replay_battle_initial_state_path == Path("custom/battle.yaml")
    assert config.replay_combat_log_path == Path("custom/combat_log.yaml")


def test_load_config_prefers_existing_replay_path_env_vars(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("REPLAY_BATTLE_INITIAL_STATE_PATH", "env/battle.yaml")
    monkeypatch.setenv("REPLAY_COMBAT_LOG_PATH", "env/combat_log.yaml")
    tmp_path.joinpath(".env").write_text(
        "REPLAY_BATTLE_INITIAL_STATE_PATH=dotenv/battle.yaml\nREPLAY_COMBAT_LOG_PATH=dotenv/combat_log.yaml\n",
        encoding="utf-8",
    )

    config = load_config()

    assert config.replay_battle_initial_state_path == Path("env/battle.yaml")
    assert config.replay_combat_log_path == Path("env/combat_log.yaml")


def test_load_config_falls_back_to_demo_replay_paths(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("REPLAY_BATTLE_INITIAL_STATE_PATH", raising=False)
    monkeypatch.delenv("REPLAY_COMBAT_LOG_PATH", raising=False)

    config = load_config()

    assert config.replay_battle_initial_state_path == DEMO_BATTLE_INITIAL_STATE_PATH
    assert config.replay_combat_log_path == DEMO_COMBAT_LOG_PATH


def test_load_config_reads_genetic_strategy_discovery_settings_from_dotenv_file(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE", raising=False)
    monkeypatch.delenv("GENETIC_STRATEGY_DISCOVERY_GENERATIONS", raising=False)
    monkeypatch.delenv("GENETIC_STRATEGY_DISCOVERY_WORKERS", raising=False)
    tmp_path.joinpath(".env").write_text(
        "GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE=12\n"
        "GENETIC_STRATEGY_DISCOVERY_GENERATIONS=5\n"
        "GENETIC_STRATEGY_DISCOVERY_WORKERS=3\n",
        encoding="utf-8",
    )

    config = load_config()

    assert config.genetic_strategy_discovery_population_size == 12
    assert config.genetic_strategy_discovery_generations == 5
    assert config.genetic_strategy_discovery_workers == 3


def test_load_config_rejects_non_positive_genetic_strategy_discovery_settings(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE", raising=False)
    tmp_path.joinpath(".env").write_text("GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE=0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE"):
        load_config()


def test_load_config_rejects_non_positive_genetic_strategy_discovery_worker_count(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GENETIC_STRATEGY_DISCOVERY_WORKERS", raising=False)
    tmp_path.joinpath(".env").write_text("GENETIC_STRATEGY_DISCOVERY_WORKERS=0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="GENETIC_STRATEGY_DISCOVERY_WORKERS"):
        load_config()


def test_load_config_falls_back_to_genetic_strategy_discovery_defaults(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE", raising=False)
    monkeypatch.delenv("GENETIC_STRATEGY_DISCOVERY_GENERATIONS", raising=False)
    monkeypatch.delenv("GENETIC_STRATEGY_DISCOVERY_WORKERS", raising=False)

    config = load_config()

    assert config.genetic_strategy_discovery_population_size == DEFAULT_GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE
    assert config.genetic_strategy_discovery_generations == DEFAULT_GENETIC_STRATEGY_DISCOVERY_GENERATIONS
    assert config.genetic_strategy_discovery_workers == DEFAULT_GENETIC_STRATEGY_DISCOVERY_WORKERS
