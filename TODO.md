# Backlog

## Entry template

```markdown
* [ ] task description
```

## Actual tasks

### Milestone 3: Range and movement math

* [x] Update `doc/requirements.md` with testable behavior for hex distance and movement radius.
* [x] Update `doc/glossary.md` with distance and movement-radius terminology if needed.
* [x] Add failing tests for distance from a coordinate to itself returning `0`.
* [x] Add failing tests for adjacent valid coordinates returning distance `1`.
* [x] Add failing tests proving distance is symmetric across staggered odd-row coordinates.
* [x] Add failing tests proving distance rejects invalid start or end coordinates.
* [x] Add failing tests for movement radius with speed `0` returning only the origin coordinate.
* [x] Add failing tests for movement radius including all valid coordinates within speed.
* [x] Add failing tests for movement radius trimming off-battlefield coordinates near edges.
* [x] Add failing tests for movement radius rejecting negative speed.
* [x] Implement `src/olden/combat/range.py` with public `distance_between()` and `movement_radius()` behavior using `HexCoord` at API boundaries.
* [x] Keep axial or cube coordinate conversion private to the range implementation.
* [x] Keep Milestone 3 scoped to pure geometric range math; do not implement line-of-sight, spell area-of-effect rings, pathfinding, movement validation, obstacles, or occupancy-aware movement.
* [x] Update `doc/development.md` with `range.py` and `test_range.py`.
* [x] Bump `pyproject.toml` version for the additive public combat API.
* [x] Update `doc/roadmap.md` after implementation to mark Milestone 3 complete only when distance and movement radius are implemented and verified.
* [x] Run `make test`.
* [x] Run `make format`.
* [x] Run `make lint`.
* [x] Run `make mypy`.
