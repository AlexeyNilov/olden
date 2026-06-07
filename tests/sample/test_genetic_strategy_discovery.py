from sample.genetic_strategy_discovery import run_genetic_strategy_discovery


def test_genetic_strategy_discovery_uses_configured_default_population_size(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE", raising=False)
    monkeypatch.delenv("GENETIC_STRATEGY_DISCOVERY_GENERATIONS", raising=False)
    tmp_path.joinpath(".env").write_text(
        "GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE=5\n"
        "GENETIC_STRATEGY_DISCOVERY_GENERATIONS=1\n"
        "GENETIC_STRATEGY_DISCOVERY_WORKERS=1\n",
        encoding="utf-8",
    )

    result = run_genetic_strategy_discovery(
        best_battle_path=tmp_path / "genetic_best_battle.yaml",
        best_combat_log_path=tmp_path / "genetic_best_combat_log.yaml",
        seed=3,
    )

    assert len(result.discovery_result.population) == 5
