# AGENTS.md

See `README.md` for the project overview and documentation map.

## Context Loading

Read only the context needed for the task. Prefer `rg` and targeted section reads over opening whole documents.

Before changing code or docs, route to the owner document:

- Combat behavior: relevant section of `doc/requirements.md`; add or update it before tests when behavior is missing or ambiguous.
- Combat-action planning: `doc/combat_system_reference.md`, then promote only committed behavior into `doc/requirements.md`.
- Combat terminology: `doc/glossary.md` only when introducing or renaming shared terms.
- Project structure and workflow: `doc/development.md`.
- Architecture, public API, dependencies, or data flow: `doc/decisions.md`.
- Future or deferred scope: `doc/roadmap.md`.
- Coordinate, range, or pathfinding math: `doc/hex_math.md`.

## Collaboration

Act as a research partner, not a cheerleader. Push back on weak assumptions, vague requirements, hidden trade-offs, and unsupported conclusions. Prefer concrete evidence, falsifiable behavior, and clear distinctions.

Before non-trivial implementation, state assumptions that affect behavior, public API, data, security, or verification. If behavior is unclear, stop and ask.

## TDD

For code changes, write or update a failing behavior test before implementation unless the change is mechanical or documentation-only. Tests should describe observable behavior, avoid testing imported libraries, and avoid over-mocking internal logic. Do not add tests for code in `sample/`.

## Project Rules

- Use existing project patterns.
- Do not duplicate long-lived facts across docs; update the canonical owner first and reference it elsewhere when needed.
- `TODO.md` owns active implementation tasks only; do not use it as a planning archive.
- `.env` is local-only and may contain user-specific credentials; never commit it.
- Bump the version in `pyproject.toml` for user-visible behavior, public API changes, or substantial domain implementation.
- Do not bump the version for documentation-only changes, tests-only changes, or internal refactors with no behavior or API change.

## Code Shape

- Use explicit and precise type hints for all arguments and return values.
- Omit docstrings for obvious functions; use Google-style docstrings only for complex why logic or non-obvious business rules.
- Keep business logic, I/O, and logging separate.
- Use logging, not print, except in CLI-only scripts.
- Avoid new dependencies unless justified.
- Do not introduce generic `models`, `services`, `repositories`, `application`, or `infrastructure` layers unless the need is concrete and documented. Prefer modules named after domain concepts.

## Combat Domain

- Treat `src/olden/combat/` as the bounded context for combat simulation.
- Keep `Battlefield` distinct from `Battle`.
- `Battlefield` is static topology and field configuration.
- `Battle state` is dynamic state such as occupancy.
- Use `HexCoord(column, row)` as the public coordinate model.
- Keep axial and cube coordinates as internal helpers for hex math unless a public API need is documented.
- Obstacles are whole-hex blockers.
- Deployment zones are side-based: player-controlled side on the left, enemy side on the right.

## Verification

For code changes, run `make test`, `make format`, `make lint`, and `make mypy` before completion. For documentation-only changes, do not run tests unless executable examples changed. Report failures with the smallest useful excerpt.
