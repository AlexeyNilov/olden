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
