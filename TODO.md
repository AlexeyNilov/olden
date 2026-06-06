# Backlog

## Entry template

```markdown
* [ ] task description
```

## Actual tasks

## Combat Field Model Plan

### Assumptions to validate

* [x] Reconcile battlefield dimensions: the field has 11 rows with alternating row lengths, totaling 137 hexes.
* [x] Confirm whether the battlefield uses flat-top or pointy-top hexes in the source game: flat-top, based on `image/field.png`.
* [x] Confirm whether odd or even rows are horizontally offset in the canonical coordinate model: odd rows are longer and contain 13 hexes.
* [x] Confirm whether coordinates exposed to users should be zero-based Python coordinates, one-based game/UI coordinates, or both: zero-based only.
* [x] Confirm whether multi-hex creatures, blocked tiles, obstacles, and deployment zones belong in the first field model or a later layer: include occupancy, obstacles, and deployment zones in the first model.
* [x] Confirm whether pathfinding belongs in the first milestone: defer pathfinding.

### Accepted decisions

* [x] The battlefield has 11 rows, addressed with zero-based coordinates.
* [x] Row lengths are `[12, 13, 12, 13, 12, 13, 12, 13, 12, 13, 12]`, totaling 137 hexes.
* [x] Odd-numbered rows contain 13 hexes; even-numbered rows contain 12 hexes.
* [x] The battlefield uses flat-top hexes.
* [x] Olden Era uses the same combat-grid conventions as older Heroes games.
* [x] The Python API should expose `HexCoord(column: int, row: int)` rather than one-based UI labels.
* [x] The first model must support field topology, occupancy, obstacles, and deployment zones.
* [x] Deployment zones are fixed by side: player-controlled side on the left, enemy side on the right.
* [x] Obstacles are always whole-hex blockers.
* [x] Pathfinding and movement range are outside the first milestone.
* [x] Future range work must support distance between hexes, movement radius by unit speed, and spell AoE rings.

### Documentation tasks

* [x] Add an initial user story to `doc/user_stories.md`: As a combat simulator developer, I want a deterministic battlefield model so that movement, targeting, and placement rules can be tested.
* [x] Add EARS requirements to `doc/requirements.md` for ragged-row battlefield dimensions, valid coordinate lookup, neighbor lookup, and invalid coordinate rejection.
* [x] Add an ADR to `doc/decisions.md` once the coordinate system is chosen.

### Candidate representations

* [x] Evaluate offset coordinates for the public API because they map naturally to a row-based battlefield, even with ragged row lengths.
* [x] Evaluate axial coordinates for internal neighbor, distance, movement range, and AoE ring calculations because hex math is simpler and less error-prone.
* [x] Evaluate cube coordinates only as a private conversion helper if distance, line-of-sight, pathfinding, or complex AoE shapes need it.

### Proposed direction

* [ ] Prefer a row-offset coordinate field as the public model: `HexCoord(column: int, row: int)`.
* [ ] Keep coordinate validation in a small `Battlefield` domain object with explicit per-row lengths, defaulting to `[12, 13, 12, 13, 12, 13, 12, 13, 12, 13, 12]`.
* [ ] Design the coordinate model so offset coordinates can convert to axial coordinates later for unit speed, distance, movement range, and spell AoE rings.
* [ ] Add conversion helpers to axial coordinates when implementing the first behavior that benefits from hex math, such as distance or rings.
* [ ] Represent each hex's static properties separately from dynamic battle state: deployment zones are field configuration; occupancy is battle state.
* [ ] Represent obstacles as field objects that occupy one or more whole-hex coordinates.
* [ ] Treat multi-hex creatures as an occupancy concern, not as a coordinate-system concern.

### TDD implementation tasks

* [ ] Write a failing test that a default battlefield exposes row lengths `[12, 13, 12, 13, 12, 13, 12, 13, 12, 13, 12]`.
* [ ] Write a failing test that a default battlefield contains exactly 137 valid coordinates.
* [ ] Write a failing test that valid edge and corner coordinates are accepted.
* [ ] Write a failing test that negative coordinates and coordinates outside each row's length are rejected before any lookup logic runs.
* [ ] Write a failing test that neighbor lookup returns only in-bounds neighboring hexes for center, edge, and corner positions.
* [ ] Write a failing test that the chosen row-offset parity matches the expected six neighbors for a known coordinate.
* [ ] Write a failing test that a hex can expose deployment-zone metadata without affecting coordinate validity.
* [ ] Write a failing test that occupancy rejects placing two units on the same coordinate.
* [ ] Write a failing test that an obstacle blocks occupancy on all coordinates it covers.
* [ ] Implement the smallest battlefield model that satisfies the tests.
* [ ] Run `make format`, `make lint`, `make mypy`, and `go test` only if relevant; for this Python project, use the Python checks listed in `AGENTS.md`.

### Clarifying questions

* [x] Is the battlefield visually flat-top or pointy-top? Flat-top.
* [x] Should the canonical coordinate exposed by the Python API be `(column, row)`, `(x, y)`, or a game-specific label? Use `(column, row)` through `HexCoord`.
* [x] Should API coordinates be zero-based, one-based, or support both with explicit conversion? Zero-based.
* [x] Does Olden Era use the same combat-grid conventions as earlier Heroes games, or should we avoid assuming inherited rules? It uses the same structure as older Heroes games.
* [x] Do we need to model only the field topology first, or should the first iteration include occupied hexes, obstacles, and deployment zones? Include occupancy, obstacles, and deployment zones.
* [x] Should pathfinding and movement range be part of the first milestone, or deferred until the static field model is tested? Deferred.
* [x] Which rows are shifted horizontally in the canonical model: odd rows or even rows? Odd rows are longer and contain 13 hexes.
* [x] How many hexes do odd rows contain? 13.
* [x] If zero-based odd rows have 13 hexes and even rows have 12 hexes, is the total battlefield size 137 hexes? Yes.
* [x] Are deployment zones fixed by side, creature type, scenario, or arbitrary scenario configuration? Fixed by side: player-controlled side on the left, enemy side on the right.
* [x] Can obstacles occupy partial hex edges, or are they always whole-hex blockers? Always whole-hex blockers.
* [x] Which future range operations should be supported first after topology: distance between hexes, movement radius by unit speed, or spell AoE rings? All of them.
