# Backlog

## Entry template

```markdown
* [ ] task description
```

## Actual tasks

### Milestone 4: Single-hex movement simulation

* [ ] Update `doc/requirements.md` with testable single-hex movement behavior before writing implementation tests.
* [ ] Update `doc/glossary.md` with movement path, passable coordinate, movement cost, and unreachable path terminology.
* [ ] Add a focused ADR to `doc/decisions.md` for Milestone 4 movement choices: single-hex scope, constant cost `1`, dedicated unreachable-path exception, validation returns a path, and occupancy mutation stays separate.
* [ ] Add failing occupancy tests for querying all coordinates occupied by a unit id.
* [ ] Add failing occupancy tests for removing a unit's occupied coordinates.
* [ ] Add failing occupancy tests for moving a single-hex unit from one coordinate to another.
* [ ] Add failing occupancy tests proving a moving unit's own current coordinate can be ignored during movement validation while other units still block.
* [ ] Add failing movement tests for shortest-path finding across unobstructed neighboring hexes.
* [ ] Add failing movement tests for pathfinding around obstacle coordinates.
* [ ] Add failing movement tests for pathfinding around occupied coordinates.
* [ ] Add failing movement tests for unreachable destinations raising a dedicated movement exception.
* [ ] Add failing movement tests for movement validation accepting destinations whose path cost is within unit speed.
* [ ] Add failing movement tests for movement validation rejecting destinations whose path cost exceeds unit speed.
* [ ] Add failing movement tests for movement validation rejecting invalid start or destination coordinates.
* [ ] Add failing movement tests for movement validation rejecting blocked or enemy-occupied destinations.
* [ ] Implement a dedicated exception for unreachable movement paths.
* [ ] Implement `src/olden/combat/movement.py` with single-hex `find_path()` and `validate_movement()` behavior.
* [ ] Use breadth-first search over `Battlefield.neighbors()` for shortest paths.
* [ ] Treat every movement step as cost `1`; path cost is `len(path) - 1`.
* [ ] Keep validation pure: return the valid path and do not mutate occupancy.
* [ ] Update `src/olden/combat/occupancy.py` with the minimal query/remove/move helpers needed for single-hex movement.
* [ ] Keep Milestone 4 scoped to single-hex footprints; defer multi-hex pathfinding and footprint clearance rules.
* [ ] Keep flying, teleporting, terrain-specific costs, attack zones, turn order, waiting, and action economy out of Milestone 4.
* [ ] Update `doc/development.md` with `movement.py` and `test_movement.py`.
* [ ] Bump `pyproject.toml` version for the additive public combat API.
* [ ] Update `doc/roadmap.md` after implementation to mark Milestone 4 complete only when single-hex movement validation, constant movement cost, and pathfinding are implemented and verified.
* [ ] Run `make test`.
* [ ] Run `make format`.
* [ ] Run `make lint`.
* [ ] Run `make mypy`.
