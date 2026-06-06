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

**Context:** The combat simulator needs a deterministic field model before movement, targeting, occupancy, obstacles, and deployment zones can be implemented. The field screenshot shows flat-top hexes arranged in staggered rows. The user clarified that the canonical row lengths are `[12, 13, 12, 13, 12, 13, 12, 13, 12, 13, 12]`, for 137 total hexes, and that the Python API should use zero-based coordinates.

**Decision:** Use `HexCoord(column: int, row: int)` as the public coordinate model. The default battlefield has 11 rows. Even-numbered rows have 12 hexes, odd-numbered rows have 13 hexes, and coordinate validation is based on each row's length. The first model includes topology, occupancy, obstacles, and deployment zones. Pathfinding and movement range are deferred.

**Alternatives considered:** A rectangular 12 by 11 grid was rejected because it would omit the longer odd rows. A rectangular 13 by 11 grid was rejected because it would introduce non-existent coordinates on even rows. Axial or cube coordinates remain useful for future hex math, but exposing them now would make the public API less direct for a row-based battlefield.

**Consequences:** Coordinate validation must be row-aware, and tests need to cover ragged-row edges instead of relying on a single width. The public API remains simple for users, while the implementation can add private axial or cube conversion helpers later if distance, rings, line-of-sight, pathfinding, or movement range need them.
