# Backlog

## Entry template

```markdown
* [ ] task description
```

## Actual tasks

### Milestone 2: Unit model

* [x] Update `doc/glossary.md` with Unit model terms: combat side, unit definition, unit stack, unit footprint, initiative, attack category, morale, and luck.
* [x] Update `doc/requirements.md` with testable Unit model behavior before writing implementation tests.
* [x] Add an ADR for using `CombatSide` as the shared side concept.
* [x] Add failing tests for `UnitDefinition` identity and speed validation.
* [x] Add failing tests for `UnitStack` side, count, and non-positive count rejection.
* [x] Add failing tests for single-hex unit footprint placement through occupancy.
* [x] Add failing tests for multi-hex footprint placement rejecting blocked secondary coordinates.
* [x] Add failing tests for multi-hex footprint placement rejecting occupied secondary coordinates.
* [x] Implement `src/olden/combat/units.py` with focused immutable value objects for unit definition, unit stack, and unit footprint.
* [x] Keep Milestone 2 unit data limited to identity, side, stack count, speed, and footprint; defer damage, initiative ordering, morale/luck probability, attack resolution, abilities, costs, growth, and upgrades.
* [x] Update `src/olden/combat/occupancy.py` so placement can reserve every coordinate in a unit footprint while preserving existing one-hex behavior.
* [x] Add a Swordsman-derived example or fixture using `id="esquire"`, `name="Swordsman"`, `speed=4`, and a one-hex footprint as a data-shape check, not a full unit database.
* [x] Bump `pyproject.toml` version for the additive public combat API.
* [x] Update `doc/roadmap.md` after implementation to mark Milestone 2 complete only when identity, side, stack data, speed, and footprint rules are implemented and verified.
* [x] Run `make test`.
* [x] Run `make format`.
* [x] Run `make lint`.
* [x] Run `make mypy`.
