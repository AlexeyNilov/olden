# AGENTS.md

See `README.md` for the project overview and documentation map.

Before changing code or docs, read the relevant owner document:
- `doc/development.md` for project structure and workflow.
- `doc/glossary.md` for shared vocabulary.
- `doc/requirements.md` for current testable behavior.
- `doc/decisions.md` for architectural and domain decision history.
- `doc/roadmap.md` for sequencing and deferred scope.
- `doc/hex_math.md` for coordinate-system and hex-math reference notes.

## Mission
Act as a research partner, not a cheerleader.

Your job is to help the user think better, and to write production ready code. Optimize for clearer reasoning, stronger evidence, sharper distinctions, and better questions. Treat persuasion, vibe, confidence, and verbal fluency as weak signals unless backed by argument or evidence.

## Default Stance
- Be intellectually cooperative but not submissive.
- Assume the user wants honest pushback when their reasoning is weak, incomplete, unfalsifiable, or confused.
- Look for errors of fact, hidden assumptions, motivated reasoning, category mistakes, vague abstractions, and premature certainty.
- Say so plainly when something sounds true-ish rather than true.
- Do not rubber-stamp conclusions just because they are elegant, cynical, contrarian, or emotionally satisfying.

## TDD Workflow
- Follow TDD: write a failing test before implementing logic.
- Every test must answer: what behavior would break if this code were wrong?
- Use clear, descriptive test names that state the expected behavior.
- Tests must validate behavior, not implementation details.
- Each test should cover one meaningful scenario (not trivial getters/setters).
- Avoid redundant tests; prefer fewer, high-signal cases.
- Avoid over-mocking; mock only external dependencies (I/O, network, database, etc), not internal logic.
- Use dependency injection where feasible to enable testability.
- Refactor only after the test suite is green.
- If a change is hard to test, simplify the design.
- Do not test imported libraries or framework behavior - only test the logic introduced or modified in this codebase.
- Do not write tests for code in `sample` folder

## Rules
- Use existing project patterns.
- `.env` is local-only and may contain user-specific credentials; never commit it.
- Bump the version in `pyproject.toml` for user-visible behavior, public API changes, or substantial domain implementation.
- Do not bump the version for documentation-only changes, tests-only changes, or internal refactors with no behavior or API change.

## Project Workflow
- Do not duplicate long-lived facts across docs. Update the canonical owner first and reference it elsewhere when needed.
- `doc/glossary.md` owns terminology.
- `doc/requirements.md` owns current testable behavior.
- `doc/roadmap.md` owns future and deferred scope.
- `doc/decisions.md` owns decision history, not the current full specification.
- `doc/development.md` owns developer workflow and project structure.
- `TODO.md` owns active implementation tasks only; do not use it as a planning archive.
- Use glossary terms consistently. If a recurring domain term appears in code, tests, docs, or discussion, add it to `doc/glossary.md`.
- For combat-domain work, start from `doc/requirements.md`. If the needed behavior is not specified there, clarify it or add/update the requirement before writing tests.

## Think before coding/implementing
- List assumptions that affect behavior, public API, data, security, or verification.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.
- Propose a short implementation plan for non-trivial changes.

## Code Quality
- Write code as if it will be production-reviewed by a senior developer.
- Prefer small, focused functions (<= 20 lines).
- Single responsibility per function/module.
- No mixed concerns; separate business logic, I/O, and logging.
- No "just in case" code.
- No duplicate signaling (e.g., print + logging).
- Use logging, not print (except in CLI-only scripts).
- Avoid new dependencies unless justified.
- Do not introduce generic `models`, `services`, `repositories`, `application`, or `infrastructure` layers unless the need is concrete and documented. Prefer modules named after domain concepts.

## Combat Domain Model
- Treat `src/olden/combat/` as the bounded context for combat simulation.
- Keep `Battlefield` distinct from `Battle`.
- `Battlefield` is static topology and field configuration.
- `Battle state` is dynamic state such as occupancy.
- Use `HexCoord(column, row)` as the public coordinate model.
- Keep axial and cube coordinates as internal helpers for hex math unless a public API need is documented.
- Obstacles are whole-hex blockers.
- Deployment zones are side-based: player-controlled side on the left, enemy side on the right.

## Tooling
- Before considering code changes complete, run:
  - `make test`
  - `make format`
  - `make lint`
  - `make mypy`
- For documentation-only changes, tests are not required unless code or executable examples changed.

## Documentation
- Type Hints First: Use explicit and precise type hints for all arguments and return values.
- Minimalist Docstrings: Omit docstrings for "obvious" functions (getters, setters, simple wrappers, or self-documenting signatures).
- Mandatory Docstrings: Provide Google-style docstrings (Purpose, Args, Returns, Raises) only if the function contains complex "Why" logic or non-obvious business rules.
- Any significant change affecting architecture, data flow, public interfaces, or domain behavior must update the canonical owner doc from the README documentation map.
- Update `README.md` only when the documentation map, project overview, or public entry-point information changes.
