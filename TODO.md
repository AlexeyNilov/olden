# Backlog

## Entry template

```markdown
* [ ] task description
```

## Actual tasks

### Milestone 5: Battlefield view

* [x] Add battlefield-view requirements for read-only field rendering, deployment-zone display, obstacle display, and unit placement display.
* [x] Record an ADR for using NiceGUI as an optional local visualization dependency isolated from the combat domain.
* [x] Add a `view` optional dependency group with `nicegui>=3.12,<4`.
* [x] Add a pure battlefield-view layout model that maps every valid `HexCoord` to stable render positions with odd-row staggering.
* [x] Add a pure battlefield-view state model that combines `Battlefield`, `Occupancy`, and optional unit metadata into renderable hex data.
* [x] Add focused tests for coordinate layout, deployment-zone rendering state, obstacle rendering state, and occupied-coordinate rendering state.
* [x] Add a read-only NiceGUI battlefield page that renders the view model without mutating combat state.
* [x] Add a documented local entry point for launching the battlefield view.
* [x] Run `make test`, `make format`, `make lint`, and `make mypy`.
