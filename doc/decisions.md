# Decisions

## Why record decisions

Write down key development decisions while the context is fresh. A short note today can save hours later by explaining what was chosen, what was rejected, and why the trade-off made sense at the time.

## Guidance

Use a lightweight Architecture Decision Record (ADR) style:

* Record decisions that affect architecture, data flow, public APIs, dependencies, deployment, security, or long-term maintenance.
* Write the decision when it is made, not after the context has faded.
* Prefer short entries that explain the context, decision, alternatives, and consequences.
* Include enough reasoning for a future maintainer to understand the trade-off.
* Do not document every small implementation detail; focus on choices that would be costly or confusing to rediscover.
* Update or supersede earlier decisions instead of silently rewriting history.
* Do not edit old ADRs just to mirror current requirements; add a new ADR when the decision changes.

## Entry template

```markdown
### YYYY-MM-DD: Decision title

**Status:** Proposed | Accepted | Superseded

**Context:** What problem, constraint, or trade-off led to this decision?

**Decision:** What was chosen?

**Alternatives considered:** What other options were rejected, and why?

**Consequences:** What becomes easier, harder, riskier, or more constrained?
```

## Actual decisions

### 2026-06-06: Use YAML battle setup and replayable combat log events

**Status:** Accepted

**Context:** Milestone 8 needs persisted battle initial state and a combat log that can be replayed later by the battlefield view. Current requirements still defer full initiative tie-breakers, waiting, attacks, spells, and damage resolution, so the first log schema needs to preserve replay data without pretending those rules exist.

**Decision:** Store battle initial state and combat logs as schema-versioned YAML. Keep battle setup loading in `combat/battle_setup.py`, keep battle-level movement orchestration in `combat/battle.py`, and keep ordered event history plus replay in `combat/combat_log.py`. Support only `battle_started` and `unit_moved` events initially. Unit movement events record sequence number, turn marker, stack ID, start coordinate, destination coordinate, and path.

**Alternatives considered:** JSON was rejected because YAML is already used for hand-maintained project data and needs no new dependency. Implementing full initiative ordering was rejected because the reference notes still have open tie-breaker questions. Adding attack or spell log event types now was rejected because those actions do not have executable combat behavior yet.

**Consequences:** Battle setup and logs are inspectable local files under a stable versioned schema. Replay can reconstruct movement state for the battlefield view. Future combat actions can add event types without changing the current movement event contract, but incompatible schema changes must be versioned.

### 2026-06-06: Use a YAML-backed local unit catalog

**Status:** Accepted

**Context:** Milestone 6 introduces static unit data and related lookup operations. Unit records need source metadata and may include stats that are not yet part of combat simulation. Some source data is licensed under CC BY-SA, while the project code is CC0.

**Decision:** Store packaged unit records in YAML and load them through a small typed unit catalog API. Keep the catalog data in a separate package area with CC BY-SA license and notice files, while keeping simulator code under the project license. Use `yaml.safe_load`, validate loaded data into explicit dataclasses, reject duplicate IDs, and convert catalog records to the narrower combat `UnitDefinition` only through an explicit method.

**Alternatives considered:** JSON was rejected because the catalog is expected to be hand-maintained and source-annotated, where comments and less punctuation are useful. SQLite was rejected because query needs are currently simple ID lookups. TOML was rejected because it is awkward for a growing list of nested records. A generic repository layer was rejected because `UnitCatalog` names the concrete domain need without adding broad infrastructure structure.

**Consequences:** The project gains one runtime dependency on PyYAML and must treat YAML parsing as an I/O boundary. Catalog dates and other string-like scalar values need validation because YAML parsers may coerce unquoted values. Bundled data can carry CC BY-SA obligations separately from CC0 code, but downstream packaging and distribution must preserve those data notices.

### 2026-06-06: Use NiceGUI for the local battlefield view

**Status:** Accepted

**Context:** Milestone 5 needs a local visualization of battlefield topology, field configuration, and unit placement. The simulator's core combat model is pure domain logic and should remain usable without a browser UI dependency. The view also needs enough layout flexibility to render a staggered flat-top hex field.

**Decision:** Use NiceGUI as an optional `view` dependency for a read-only local battlefield view. Keep the NiceGUI integration outside `src/olden/combat/` and put testable layout and render-state mapping in pure Python modules that do not import NiceGUI.

**Alternatives considered:** A static SVG or HTML export was rejected because it would not give a natural path toward interactive inspection. Matplotlib was rejected because it is better suited to plotting than browser-based UI controls. A full JavaScript frontend was rejected because it would add a second application stack before interaction requirements exist.

**Consequences:** The combat domain remains independent of the UI package, while developers can launch a local browser view with the optional extra installed. UI behavior must stay read-only until interaction requirements are added.

### 2026-06-06: Scope first movement simulation to single-hex pathfinding

**Status:** Accepted

**Context:** Milestone 4 introduces movement validation, constant movement cost, and pathfinding. The simulator already has unit footprints, obstacles, occupancy, neighbor lookup, and range math, but multi-hex movement adds footprint-clearance complexity that is not needed for the first movement slice.

**Decision:** Implement Milestone 4 as single-hex movement only. Each adjacent step costs `1`, so path cost is `len(path) - 1`. Pathfinding uses breadth-first search over battlefield neighbors and treats obstacles and other units as impassable. A moving unit may pass through its own starting coordinate. Unreachable destinations raise a dedicated movement exception. Movement validation returns the valid path and does not mutate occupancy; occupancy mutation remains a separate operation.

**Alternatives considered:** Implementing multi-hex movement now was rejected because it requires additional rules for rotating or translating footprints through narrow spaces. Returning an empty path for unreachable destinations was rejected because unreachable movement is an exceptional validation outcome that callers should handle explicitly. Combining validation with occupancy mutation was rejected because it would mix path calculation with battle-state mutation.

**Consequences:** The first movement API stays small and testable. Movement can route around blockers and occupied hexes for single-hex units. Future multi-hex movement will need separate requirements and tests for footprint clearance along the whole path.

### 2026-06-06: Use combat side as the shared side vocabulary

**Status:** Accepted

**Context:** Milestone 1 introduced side-based deployment zones before unit stacks existed. Milestone 2 needs side data on unit stacks as battle state, not only deployment configuration. Using deployment-specific side naming for units would blur field configuration with dynamic combat state, while adding a separate unit-side enum would duplicate the same two-sided concept.

**Decision:** Use `CombatSide` as the shared public side enum for combat concepts, including deployment zones and unit stacks.

**Alternatives considered:** Using deployment-specific side naming everywhere was rejected because units are not deployment zones. Creating a separate unit-side enum was rejected because the current simulator has one side concept, and duplicating it would force unnecessary conversion between equivalent values.

**Consequences:** Deployment zones and unit stacks use one side vocabulary. Pre-release callers must import `CombatSide` for side-based combat APIs. If future rules distinguish attacker/defender from player/enemy, that role concept should be added separately rather than overloading `CombatSide`.

### 2026-06-06: Represent the battlefield with zero-based row-offset coordinates

**Status:** Accepted

**Context:** The combat simulator needs a deterministic field model before movement, targeting, occupancy, obstacles, and deployment zones can be implemented. The field screenshot shows flat-top hexes arranged in staggered rows. The user clarified that the canonical row lengths are `[12, 13, 12, 13, 12, 13, 12, 13, 12, 13, 12]`, for 137 total hexes, that the Python API should use zero-based coordinates, and that Olden Era follows older Heroes combat-grid conventions.

**Decision:** Use `HexCoord(column: int, row: int)` as the public coordinate model. The default battlefield has 11 rows. Even-numbered rows have 12 hexes, odd-numbered rows have 13 hexes, and coordinate validation is based on each row's length. The first model includes topology, occupancy, whole-hex obstacles, and side-fixed deployment zones with the player-controlled side on the left and the enemy side on the right. Pathfinding and movement range are deferred.

**Alternatives considered:** A rectangular 12 by 11 grid was rejected because it would omit the longer odd rows. A rectangular 13 by 11 grid was rejected because it would introduce non-existent coordinates on even rows. Axial or cube coordinates remain useful for future hex math, but exposing them now would make the public API less direct for a row-based battlefield.

**Consequences:** Coordinate validation must be row-aware, and tests need to cover ragged-row edges instead of relying on a single width. The public API remains simple for users, while the implementation can add private axial or cube conversion helpers later for distance between hexes, movement radius by unit speed, spell AoE rings, line-of-sight, or pathfinding.

### 2026-06-06: Use a lightweight domain-first package structure

**Status:** Accepted

**Context:** The project is greenfield, but the combat simulator already has real domain concepts: battlefield topology, coordinates, occupancy, obstacles, deployment zones, future movement ranges, spell areas, and pathfinding. A completely flat module layout would likely become hard to navigate. A full DDD structure with repositories, factories, application services, infrastructure adapters, and generic model/service folders would add ceremony before the project has persistence, external I/O, or use-case orchestration.

**Decision:** Use `src/olden/combat/` as the combat simulation bounded context. Split modules by domain concept: `coordinates.py`, `battlefield.py`, `occupancy.py`, `obstacles.py`, and `deployment.py`. Keep the first implementation as pure domain logic. Add service modules only when behavior does not naturally belong to one domain object. Add infrastructure modules only when the project has real I/O such as persistence, API handlers, CLI commands, or file loading.

**Alternatives considered:** A flat package was rejected because coordinate math, topology, occupancy, obstacles, and deployment rules are separate enough to deserve clear modules. A full layered DDD package structure was rejected because layers like repositories, application services, and infrastructure adapters would be speculative at this stage. Generic folders such as `models/` and `services/` were rejected because they hide domain meaning and tend to collect unrelated code.

**Consequences:** The codebase gets clear domain boundaries without paying the full DDD tax. Tests can target focused modules. Future features such as movement range, spell AoE rings, line-of-sight, and pathfinding can be added in domain-specific modules when needed. If persistence or external interfaces appear later, the structure can grow into application and infrastructure layers with concrete reasons.
