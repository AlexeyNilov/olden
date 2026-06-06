# Backlog

## Entry template

```markdown
* [ ] task description
```

## Actual tasks

### Milestone 4: Single-hex movement simulation

* [x] Update `doc/requirements.md` with testable single-hex movement behavior before writing implementation tests.
* [x] Update `doc/glossary.md` with movement path, passable coordinate, movement cost, and unreachable path terminology.
* [x] Add a focused ADR to `doc/decisions.md` for Milestone 4 movement choices: single-hex scope, constant cost `1`, dedicated unreachable-path exception, validation returns a path, and occupancy mutation stays separate.
* [x] Add failing occupancy tests for querying all coordinates occupied by a unit id.
* [x] Add failing occupancy tests for removing a unit's occupied coordinates.
* [x] Add failing occupancy tests for moving a single-hex unit from one coordinate to another.
* [x] Add failing occupancy tests proving a moving unit's own current coordinate can be ignored during movement validation while other units still block.
* [x] Add failing movement tests for shortest-path finding across unobstructed neighboring hexes.
* [x] Add failing movement tests for pathfinding around obstacle coordinates.
* [x] Add failing movement tests for pathfinding around occupied coordinates.
* [x] Add failing movement tests for unreachable destinations raising a dedicated movement exception.
* [x] Add failing movement tests for movement validation accepting destinations whose path cost is within unit speed.
* [x] Add failing movement tests for movement validation rejecting destinations whose path cost exceeds unit speed.
* [x] Add failing movement tests for movement validation rejecting invalid start or destination coordinates.
* [x] Add failing movement tests for movement validation rejecting blocked or enemy-occupied destinations.
* [x] Implement a dedicated exception for unreachable movement paths.
* [x] Implement `src/olden/combat/movement.py` with single-hex `find_path()` and `validate_movement()` behavior.
* [x] Use breadth-first search over `Battlefield.neighbors()` for shortest paths.
* [x] Treat every movement step as cost `1`; path cost is `len(path) - 1`.
* [x] Keep validation pure: return the valid path and do not mutate occupancy.
* [x] Update `src/olden/combat/occupancy.py` with the minimal query/remove/move helpers needed for single-hex movement.
* [x] Keep Milestone 4 scoped to single-hex footprints; defer multi-hex pathfinding and footprint clearance rules.
* [x] Keep flying, teleporting, terrain-specific costs, attack zones, turn order, waiting, and action economy out of Milestone 4.
* [x] Update `doc/development.md` with `movement.py` and `test_movement.py`.
* [x] Bump `pyproject.toml` version for the additive public combat API.
* [x] Update `doc/roadmap.md` after implementation to mark Milestone 4 complete only when single-hex movement validation, constant movement cost, and pathfinding are implemented and verified.
* [x] Run `make test`.
* [x] Run `make format`.
* [x] Run `make lint`.
* [x] Run `make mypy`.
