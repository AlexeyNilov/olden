# Backlog

## Entry template

```markdown
* [ ] task description
```

## Actual tasks

### Milestone 2: Unit model

* [ ] Update `doc/glossary.md` with Unit model terms: combat side, unit definition, unit stack, unit footprint, initiative, attack category, morale, and luck.
* [ ] Update `doc/requirements.md` with testable Unit model behavior before writing implementation tests.
* [ ] Add an ADR to `doc/decisions.md` if replacing `DeploymentSide` with a shared combat-side concept becomes the chosen public API direction.
* [ ] Add failing tests for `UnitDefinition` identity and speed validation.
* [ ] Add failing tests for `UnitStack` side, count, and non-positive count rejection.
* [ ] Add failing tests for single-hex unit footprint placement through occupancy.
* [ ] Add failing tests for multi-hex footprint placement rejecting blocked secondary coordinates.
* [ ] Add failing tests for multi-hex footprint placement rejecting occupied secondary coordinates.
* [ ] Implement `src/olden/combat/units.py` with focused immutable value objects for unit definition, unit stack, and unit footprint.
* [ ] Keep Milestone 2 unit data limited to identity, side, stack count, speed, and footprint; defer damage, initiative ordering, morale/luck probability, attack resolution, abilities, costs, growth, and upgrades.
* [ ] Update `src/olden/combat/occupancy.py` so placement can reserve every coordinate in a unit footprint while preserving existing one-hex behavior.
* [ ] Add a Swordsman-derived example or fixture using `id="esquire"`, `name="Swordsman"`, `speed=4`, and a one-hex footprint as a data-shape check, not a full unit database.
* [ ] Bump `pyproject.toml` version for the additive public combat API.
* [ ] Update `doc/roadmap.md` after implementation to mark Milestone 2 complete only when identity, side, stack data, speed, and footprint rules are implemented and verified.
* [ ] Run `make test`.
* [ ] Run `make format`.
* [ ] Run `make lint`.
* [ ] Run `make mypy`.
