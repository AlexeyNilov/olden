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

## Milestone 8: Battlefield state and combat log

**Status:** Done

* Minimal round and turn markers for replay metadata
* Save/load battle initial state from/to YAML files in the `data` folder
* Save/load combat log events for battle start and unit movement
* Replay combat logs from battle initial state to reconstruct movement occupancy
* Render loaded battle state through the battlefield view model

## Milestone 9: Movement-only battle simulation

**Status:** Done

* Fixed two-stack movement order without initiative
* Random tie-breaking among equally short engagement paths
* Turn-by-turn movement until adjacent engagement
* Replayable movement combat log

## Milestone 10: Combat log replay view

**Status:** Done

* Separate combat replay view app
* Replay frame generation from initial battle state and combat log
* Event-by-event battlefield rendering
* Configurable playback delay
* Playback controls for play, pause, restart, previous, and next


## Milestone 11: Combat actions: Melee attack

**Status:** Done

* Review `doc/combat_system_reference.md`
* Attack targeting
* Damage resolution
* Counter attack

## Milestone 12: Combat simulation

**Status:** Done

* Rename `sample/demo_movement_simulation.py` to `sample/demo_simulation.py`
* Add the melee combat simulation to `sample/demo_simulation.py` 
* Log attacks in the combat log

## Milestone 13: Combat simulation view

**Status:** Next

* How do we show attacks using `src/olden/battlefield_view/replay_app.py`
* Add combat log window to the right side of the view
* The combat log window must be scrollable


## Milestone ?: Use genetic algorithm for combat strategy optimization/discovery

**Status:** Later

* NPC combat strategy

## Future plans

* Later concern: decide whether movement-only simulation should remain separate
  or be consolidated with the full combat simulation once both paths stabilize