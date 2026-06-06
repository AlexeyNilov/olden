# Project roadmap

## Status legend

* **Done:** Implemented and verified.
* **Next:** Expected next implementation focus.
* **Later:** Planned but not next.

## Milestone 1: Battlefield model

**Status:** Done

* Battlefield topology
* Coordinate validation
* Neighbor lookup
* Whole-hex obstacles
* Side-based deployment zones
* Occupancy rules

## Milestone 2: Unit model

**Status:** Done

* Unit identity
* Unit side
* Unit stack data
* Unit speed
* Multi-hex unit footprint rules

## Milestone 3: Range and movement math

**Status:** Done

* Distance between two hexes
* Movement radius by unit speed

## Milestone 4: Movement simulation

**Status:** Done

* Single-hex movement validation with obstacles and occupancy
* Movement cost rules
* Pathfinding

## Milestone 5: Battlefield view

**Status:** Next

* Field rendering
* Unit placement display

## Milestone 5: Data layer

**Status:** Later

* Unit database and related operations
* Repository pattern

## Milestone 6: Combat actions

**Status:** Later

* Attack targeting
* Damage resolution
* Turn-order integration