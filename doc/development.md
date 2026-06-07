# Development guide

## Architecture overview

The project uses a lightweight domain-first structure. It borrows the useful
parts of Domain-Driven Design without adding service, repository, application,
or infrastructure layers before the code needs them.

Olden is a Python combat simulator organized around a pure combat domain and
separate modules for data loading, visualization, and developer workflow.
Clean information architecture is part of the system design: each long-lived
fact should have one owner, current-state docs should stay separate from
decision history, and module names should reflect domain concepts instead of
generic layers. Shared domain vocabulary lives in `doc/glossary.md`; keep code,
tests, and docs aligned with those terms.

* `src/olden/combat/` contains combat simulation rules and should not depend on
  browser UI, local server management, or packaged data loading.
* `src/olden/unit_data/` loads and validates packaged unit catalog data, then
  converts catalog records into narrower combat-domain unit definitions.
* `src/olden/battlefield_view/` maps combat state into read-only render data and
  owns the local replay browser view.
* `data/` stores local demo battle setup and combat-log YAML files.
* `findings/` stores exploratory notes from local experiments and analysis.
* `scripts/` contains developer workflow helpers, not domain logic.
* `sample/` contains runnable examples.

Decision rationale and superseded choices live in `doc/decisions.md`; do not use
the ADR log as the current architecture specification.

## Project structure

Current layout:

```text
AGENTS.md
README.md
Makefile
TODO.md
LICENSE
.env.example
.gitignore
pyproject.toml

data/
    demo_battle.yaml
    demo_combat_log.yaml
    demo_movement_log.yaml

findings/
    stack_split_tactic.md

doc/
    combat_system_reference.md
    decisions.md
    development.md
    glossary.md
    hex_math.md
    ideas.md
    requirements.md
    roadmap.md
    simulation_setup.md

image/
    field.png

sample/
    __init__.py
    demo_simulation.py

scripts/
    __init__.py
    view_server.py

src/olden/
    __init__.py
    config.py
    exceptions.py

    battlefield_view/
        __init__.py
        layout.py
        model.py
        replay_app.py
        svg.py
        unit_images.py

    unit_data/
        __init__.py
        catalog.py
        packaged.py
        units.yaml
        LICENSE-CC-BY-SA-4.0.md
        NOTICE.md

    combat/
        __init__.py
        attack.py
        battle.py
        battle_setup.py
        battlefield.py
        combat_simulation.py
        combat_log.py
        combat_replay.py
        coordinates.py
        occupancy.py
        obstacles.py
        deployment.py
        movement.py
        range.py
        sides.py
        units.py

tests/
    test_config.py

    battlefield_view/
        test_layout.py
        test_model.py
        test_replay_app.py
        test_svg.py
        test_unit_images.py

    scripts/
        test_view_server.py

    sample/
        test_demo_simulation.py

    combat/
        test_battle_setup.py
        test_battlefield.py
        test_combat_log.py
        test_combat_simulation.py
        test_combat_replay.py
        test_movement.py
        test_occupancy.py
        test_range.py
        test_units.py

    unit_data/
        test_catalog.py
```

## Structure principles

* `src/olden/combat/` is the combat simulation bounded context.
* Modules are named after domain concepts, not generic layers.
* Keep combat-domain behavior as pure domain logic where possible.
* Put coordinate value objects and future hex-math helpers in `coordinates.py`.
* Put battlefield topology, row validation, and neighbor lookup in `battlefield.py`.
* Put dynamic unit placement rules in `occupancy.py`.
* Put movement validation and pathfinding rules in `movement.py`.
* Put blocked-coordinate rules in `obstacles.py`.
* Put deployment-zone rules in `deployment.py`.
* Put pure distance and movement-radius calculations in `range.py`.
* Put shared combat side vocabulary in `sides.py`.
* Put battle-level state orchestration in `battle.py`.
* Put melee attack targeting and damage resolution in `attack.py`.
* Put full two-stack combat simulation rules in `combat_simulation.py`.
* Put battle initial-state YAML loading and saving in `battle_setup.py`.
* Put replayable combat-event history and replay behavior in `combat_log.py`.
* Put combat-log replay frame generation in `combat_replay.py`.
* Put unit definitions and stacks in `units.py`.
* Put read-only battlefield visualization layout and render-state mapping in `src/olden/battlefield_view/`.
* Put the separate local combat replay browser view in `src/olden/battlefield_view/replay_app.py`.
* Put shared SVG battlefield rendering in `src/olden/battlefield_view/svg.py`.
* Put local packaged unit catalog loading, validation, and source-attributed data in `src/olden/unit_data/`.
* Put local battle setup examples in `data/`.
* Put exploratory findings from local experiments and analysis in `findings/`.
* Put source/reference images in `image/`.
* Put runnable local examples in `sample/`.
* Put local developer workflow scripts in `scripts/`.
* Add service modules only when behavior does not naturally belong to one domain object.
* Add infrastructure modules only when there is real I/O, such as persistence, API handlers, CLI commands, or file loading.

## Documentation workflow

* Update `doc/glossary.md` when a shared term is introduced or renamed.
* Update `doc/requirements.md` when behavior is committed enough to test.
* Update `doc/roadmap.md` when sequencing, future scope, or milestone status changes.
* Add or update files in `findings/` for exploratory observations, experiment
  summaries, and analysis that should be preserved but should not yet become
  requirements, roadmap items, or decisions.
* Update `TODO.md` only for active implementation tasks.
* Add a new ADR in `doc/decisions.md` when a choice affects architecture, data flow, public APIs, dependencies, or long-term maintenance.
* Do not edit old ADRs just to mirror current requirements; supersede them when the decision changes.
