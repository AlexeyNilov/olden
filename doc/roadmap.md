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

**Status:** Done

* Field rendering
* Unit placement display

## Milestone 6: Data layer

**Status:** Done

* Unit database and related operations
* Local YAML-backed unit catalog
* Packaged CC BY-SA unit data boundary

## Milestone 7: Battlefield unit image

**Status:** Done

* _demo_stack: use load_packaged_unit_catalog() to load the swordsman (by id esquire)
* How do we name unit image in the battlefield view? Unit image? Update the glosary
* Use picture image/esquire.webp (the file name is the same as the unit id) as the unit image if the file exists, otherwise show the name
* Show only stack count above the unit image (no need to show the name because we can see the image)


## Milestone 8: Battlefield movement view

**Status:** Later

* How do we implement movement?
* Turn-order integration


## Milestone 9: Combat actions

**Status:** Later

* Attack targeting
* Damage resolution

## Milestone ?: Combat simulation
## Milestone ?: Use genetic algorithm for combat strategy optimization/discovery

## Backlog

Combat log window, combat replay,  counter attack count, npc combat strategy with codex
