# olden

Heroes of Might and Magic: Olden Era combat simulator.

## Project structure

The project uses a lightweight domain-first structure. It borrows the useful
parts of Domain-Driven Design without adding service, repository, application,
or infrastructure layers before the code needs them.

Planned combat-domain layout:

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

tests/
    combat/
        test_battlefield.py
        test_coordinates.py
        test_occupancy.py
        test_obstacles.py
```

### Structure principles

* `combat/` is the combat simulation bounded context.
* Modules are named after domain concepts, not generic layers.
* Keep the first implementation as pure domain logic where possible.
* Put coordinate value objects and future hex-math helpers in `coordinates.py`.
* Put battlefield topology, row validation, and neighbor lookup in `battlefield.py`.
* Put dynamic unit placement rules in `occupancy.py`.
* Put blocked-coordinate rules in `obstacles.py`.
* Put deployment-zone rules in `deployment.py`.
* Add service modules only when behavior does not naturally belong to one domain object.
* Add infrastructure modules only when there is real I/O, such as persistence, API handlers, CLI commands, or file loading.

## Configuration

The server reads local configuration from `.env`. Values already set in the process
environment take precedence over `.env` values.
