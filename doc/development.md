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

    combat/
        __init__.py
        battlefield.py
        coordinates.py
        occupancy.py
        obstacles.py
        deployment.py
        range.py
        sides.py
        units.py

tests/
    test_config.py

    combat/
        test_battlefield.py
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
* Put blocked-coordinate rules in `obstacles.py`.
* Put deployment-zone rules in `deployment.py`.
* Put pure distance and movement-radius calculations in `range.py`.
* Put shared combat side vocabulary in `sides.py`.
* Put unit definitions, stacks, and footprint value objects in `units.py`.
* Add service modules only when behavior does not naturally belong to one domain object.
* Add infrastructure modules only when there is real I/O, such as persistence, API handlers, CLI commands, or file loading.

## Documentation workflow

* Update `doc/glossary.md` when a shared term is introduced or renamed.
* Update `doc/requirements.md` when behavior is committed enough to test.
* Update `doc/roadmap.md` when sequencing, future scope, or milestone status changes.
* Update `TODO.md` only for active implementation tasks.
* Add a new ADR in `doc/decisions.md` when a choice affects architecture, data flow, public APIs, dependencies, or long-term maintenance.
* Do not edit old ADRs just to mirror current requirements; supersede them when the decision changes.
