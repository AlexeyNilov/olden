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
* [x] Confirm whether multi-hex creatures, blocked tiles, obstacles, deployment zones, and terrain modifiers belong in the first field model or a later layer: include occupancy, obstacles, terrain, and deployment zones in the first model.
* [x] Confirm whether pathfinding belongs in the first milestone: defer pathfinding.

### Accepted decisions

* [x] The battlefield has 11 rows, addressed with zero-based coordinates.
* [x] Row lengths are `[12, 13, 12, 13, 12, 13, 12, 13, 12, 13, 12]`, totaling 137 hexes.
* [x] Odd-numbered rows contain 13 hexes; even-numbered rows contain 12 hexes.
* [x] The battlefield uses flat-top hexes.
* [x] The Python API should expose `HexCoord(column: int, row: int)` rather than one-based UI labels.
* [x] The first model must support field topology, occupancy, obstacles, terrain, and deployment zones.
* [x] Pathfinding and movement range are outside the first milestone.

### Documentation tasks

* [x] Add an initial user story to `doc/user_stories.md`: As a combat simulator developer, I want a deterministic battlefield model so that movement, targeting, and placement rules can be tested.
* [x] Add EARS requirements to `doc/requirements.md` for ragged-row battlefield dimensions, valid coordinate lookup, neighbor lookup, and invalid coordinate rejection.
* [x] Add an ADR to `doc/decisions.md` once the coordinate system is chosen.

### Candidate representations

* [ ] Evaluate offset coordinates for the public API because they map naturally to a row-based battlefield, even with ragged row lengths.
* [ ] Evaluate axial coordinates for internal neighbor and distance calculations because hex math is simpler and less error-prone.
* [ ] Evaluate cube coordinates only as a private conversion helper if distance, line-of-sight, or pathfinding needs become complex.

### Proposed direction

* [ ] Prefer a row-offset coordinate field as the public model: `HexCoord(column: int, row: int)`.
* [ ] Keep coordinate validation in a small `Battlefield` domain object with explicit per-row lengths, defaulting to `[12, 13, 12, 13, 12, 13, 12, 13, 12, 13, 12]`.
* [ ] Add conversion helpers to axial coordinates only when implementing behavior that benefits from hex math, such as distance or rings.
* [ ] Represent each hex's static properties separately from dynamic battle state: terrain and deployment zones are field configuration; occupancy is battle state.
* [ ] Represent obstacles as field objects that occupy one or more coordinates, rather than as a boolean flag on `Hex`, unless requirements prove obstacles are always single-hex.
* [ ] Treat multi-hex creatures as an occupancy concern, not as a coordinate-system concern.

### TDD implementation tasks

* [ ] Write a failing test that a default battlefield exposes row lengths `[12, 13, 12, 13, 12, 13, 12, 13, 12, 13, 12]`.
* [ ] Write a failing test that a default battlefield contains exactly 137 valid coordinates.
* [ ] Write a failing test that valid edge and corner coordinates are accepted.
* [ ] Write a failing test that negative coordinates and coordinates outside each row's length are rejected before any lookup logic runs.
* [ ] Write a failing test that neighbor lookup returns only in-bounds neighboring hexes for center, edge, and corner positions.
* [ ] Write a failing test that the chosen row-offset parity matches the expected six neighbors for a known coordinate.
* [ ] Write a failing test that a hex can expose terrain and deployment-zone metadata without affecting coordinate validity.
* [ ] Write a failing test that occupancy rejects placing two units on the same coordinate.
* [ ] Write a failing test that an obstacle blocks occupancy on all coordinates it covers.
* [ ] Implement the smallest battlefield model that satisfies the tests.
* [ ] Run `make format`, `make lint`, `make mypy`, and `go test` only if relevant; for this Python project, use the Python checks listed in `AGENTS.md`.

### Clarifying questions

* [x] Is the battlefield visually flat-top or pointy-top? Flat-top.
* [x] Should the canonical coordinate exposed by the Python API be `(column, row)`, `(x, y)`, or a game-specific label? Use `(column, row)` through `HexCoord`.
* [x] Should API coordinates be zero-based, one-based, or support both with explicit conversion? Zero-based.
* [ ] Does Olden Era use the same combat-grid conventions as earlier Heroes games, or should we avoid assuming inherited rules?
* [x] Do we need to model only the field topology first, or should the first iteration include occupied hexes, obstacles, deployment zones, and terrain effects? Include occupancy, obstacles, deployment zones, and terrain.
* [x] Should pathfinding and movement range be part of the first milestone, or deferred until the static field model is tested? Deferred.
* [x] Which rows are shifted horizontally in the canonical model: odd rows or even rows? Odd rows are longer and contain 13 hexes.
* [x] How many hexes do odd rows contain? 13.
* [x] If zero-based odd rows have 13 hexes and even rows have 12 hexes, is the total battlefield size 137 hexes? Yes.
* [ ] Are deployment zones fixed by side, creature type, scenario, or arbitrary scenario configuration?
* [ ] What terrain categories are needed for the first iteration: visual-only labels, movement modifiers, combat modifiers, or both movement and combat modifiers?
* [ ] Can obstacles occupy partial hex edges, or are they always whole-hex blockers?
