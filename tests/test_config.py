import logging
from pathlib import Path

import pytest

from olden.config import DEMO_BATTLE_INITIAL_STATE_PATH, DEMO_COMBAT_LOG_PATH, load_config


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
