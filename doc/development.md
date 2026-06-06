# Development guide

## Project structure

The project uses a lightweight domain-first structure. It borrows the useful
parts of Domain-Driven Design without adding service, repository, application,
or infrastructure layers before the code needs them.

Combat-domain layout:

```text
src/olden/
    __init__.py
    config.py
    exceptions.py

    battlefield_view/
        __init__.py
        layout.py
        model.py
        replay_app.py
        static.py
        unit_images.py

    unit_data/
        __init__.py
        catalog.py
        packaged.py
        units.yaml

scripts/
    view_server.py

    combat/
        __init__.py
        battle.py
        battle_setup.py
        battlefield.py
        combat_log.py
        combat_replay.py
        coordinates.py
        movement_simulation.py
        occupancy.py
        obstacles.py
        deployment.py
        movement.py
        range.py
        sides.py
        units.py

tests/
    test_config.py

    sample/
        test_demo_movement_simulation.py

    combat/
        test_battle_setup.py
        test_battlefield.py
        test_combat_log.py
        test_movement.py
        test_occupancy.py
        test_range.py
        test_units.py
```

## Structure principles

* `combat/` is the combat simulation bounded context.
* Modules are named after domain concepts, not generic layers.
* Keep the first implementation as pure domain logic where possible.
* Put coordinate value objects and future hex-math helpers in `coordinates.py`.
* Put battlefield topology, row validation, and neighbor lookup in `battlefield.py`.
* Put dynamic unit placement rules in `occupancy.py`.
* Put movement validation and pathfinding rules in `movement.py`.
* Put movement-only battle simulation rules in `movement_simulation.py`.
* Put blocked-coordinate rules in `obstacles.py`.
* Put deployment-zone rules in `deployment.py`.
* Put pure distance and movement-radius calculations in `range.py`.
* Put shared combat side vocabulary in `sides.py`.
* Put battle-level state orchestration in `battle.py`.
* Put battle initial-state YAML loading and saving in `battle_setup.py`.
* Put replayable combat-event history and replay behavior in `combat_log.py`.
* Put combat-log replay frame generation in `combat_replay.py`.
* Put unit definitions, stacks, and footprint value objects in `units.py`.
* Put read-only battlefield visualization layout and render-state mapping in `battlefield_view/`.
* Put the static local battlefield browser view in `battlefield_view/static.py`.
* Put the separate local combat replay browser view in `battlefield_view/replay_app.py`.
* Put local packaged unit catalog loading, validation, and source-attributed data in `unit_data/`.
* Put local battle setup examples in `data/`.
* Put runnable local examples in `sample/`.
* Put local developer workflow scripts in `scripts/`.
* Add service modules only when behavior does not naturally belong to one domain object.
* Add infrastructure modules only when there is real I/O, such as persistence, API handlers, CLI commands, or file loading.

## Documentation workflow

* Update `doc/glossary.md` when a shared term is introduced or renamed.
* Update `doc/requirements.md` when behavior is committed enough to test.
* Update `doc/roadmap.md` when sequencing, future scope, or milestone status changes.
* Update `TODO.md` only for active implementation tasks.
* Add a new ADR in `doc/decisions.md` when a choice affects architecture, data flow, public APIs, dependencies, or long-term maintenance.
* Do not edit old ADRs just to mirror current requirements; supersede them when the decision changes.
