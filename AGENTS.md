# AGENTS.md

See `README.md` for the project overview and documentation map.

## Context Loading

Read only the context needed for the task. Prefer `rg` and targeted section reads over opening whole documents.
Do not pre-read broad project docs, owner docs, or wiki captures "just in case";
open them only when the task directly depends on their content. Use search
results, file names, and narrow excerpts to decide whether a document is
relevant before reading more.

Before changing code or docs, route to the owner document:

- Combat behavior: relevant section of `doc/requirements.md`; add or update it before tests when behavior is missing or ambiguous.
- Combat-action planning: `doc/wiki/combat_system_reference.md`, then promote only committed behavior into `doc/requirements.md`.
- Combat terminology: `doc/glossary.md` only when introducing or renaming shared terms.
- Current local simulation and strategy-discovery setup: `doc/simulation_setup.md`.
- Current architecture, project structure, and workflow: `doc/development.md`.
- Decision history: `doc/decisions.md`.
- Exploratory findings from local experiments or analysis: `findings/`.
- Future or deferred scope: `doc/roadmap.md`.

## Collaboration

Act as a research partner, not a cheerleader. Push back on weak assumptions, vague requirements, hidden trade-offs, and unsupported conclusions. Prefer concrete evidence, falsifiable behavior, and clear distinctions.

Before non-trivial implementation, state assumptions that affect behavior, public API, data, security, or verification. If behavior is unclear, stop and ask.

## TDD

For code changes, write or update a failing behavior test before implementation unless the change is mechanical or documentation-only. Tests should describe observable behavior, avoid testing imported libraries, and avoid over-mocking internal logic. Do not add tests for code in `sample/`.

## Project Rules

- Use existing project patterns.
- Follow the documentation workflow in `doc/development.md`: do not duplicate long-lived facts across docs; update the canonical owner first and reference it elsewhere when needed.
- Use glossary terms consistently in code, tests, and docs; when a recurring domain term is introduced or renamed, update `doc/glossary.md`.
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

## Combat Invariants

Keep only high-risk combat constraints here; read owner docs for full behavior.

- `src/olden/combat/` owns combat simulation rules; visualization and catalog loading stay outside that bounded context.
- Keep `Battlefield` distinct from `Battle`: battlefield is static topology/configuration; battle state is dynamic combat state.
- Use `HexCoord(column, row)` at public boundaries and in behavior tests. Keep axial/cube coordinates internal unless a public API need is documented.
- Do not implement deferred combat mechanics from reference notes until committed behavior exists in `doc/requirements.md`.

## Python Environment

- Use the project virtualenv for every direct Python invocation: `.venv/bin/python` on Unix, `.venv/Scripts/python.exe` on Windows (same paths as the Makefile `PYTHON` variable).
- Do not probe `python`, `python3`, or system Python first; the package is installed editable in `.venv` only.

## Verification

For code changes, run `make test`, `make format`, `make lint`, and `make mypy` before completion. For documentation-only changes, do not run tests unless executable examples changed. Report failures with the smallest useful excerpt.
