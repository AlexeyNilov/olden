# Requirements

## EARS (Easy Approach to Requirements Syntax)

Use the EARS structure for precise requirements:

> **While** `<optional precondition>`, **when** `<optional trigger>`, **the system shall** `<system response>`.

This helps ensure requirements are:

* Context-aware
* Trigger-based
* Action-specific

## Actual requirements

### Battlefield topology

* **When** the default battlefield is created, **the system shall** create 11 zero-based rows.
* **When** the default battlefield is created, **the system shall** use row lengths `[12, 13, 12, 13, 12, 13, 12, 13, 12, 13, 12]`.
* **When** the default battlefield is created, **the system shall** expose exactly 137 valid hex coordinates.
* **When** a coordinate is represented in the Python API, **the system shall** use zero-based `column` and `row` values.
* **When** the battlefield topology is represented, **the system shall** model flat-top hexes with staggered odd-numbered rows.

### Coordinate validation

* **When** a coordinate has a negative row or column, **the system shall** reject it as invalid.
* **When** a coordinate row is outside `0..10`, **the system shall** reject it as invalid.
* **When** a coordinate column is outside the valid range for that coordinate's row length, **the system shall** reject it as invalid.
* **When** a coordinate is valid, **the system shall** allow lookup of that coordinate's field data.

### Neighbor lookup

* **When** neighbor lookup is requested for a valid interior coordinate, **the system shall** return the six adjacent in-bounds hex coordinates.
* **When** neighbor lookup is requested for a valid edge or corner coordinate, **the system shall** return only adjacent hex coordinates that exist on the battlefield.
* **When** neighbor lookup is requested for an invalid coordinate, **the system shall** reject the request before calculating neighbors.

### Field state

* **When** field configuration is represented, **the system shall** keep deployment-zone data separate from dynamic unit occupancy.
* **When** obstacles are represented, **the system shall** support obstacles that cover one or more hex coordinates.
* **When** obstacles are represented, **the system shall** treat each obstacle coordinate as a whole-hex blocker.
* **When** a unit occupies a coordinate, **the system shall** prevent another unit from occupying the same coordinate at the same time.
* **When** a coordinate is covered by an obstacle, **the system shall** prevent unit occupancy on that coordinate.
* **While** pathfinding and movement range are deferred, **the system shall** avoid exposing pathfinding or movement-range APIs as part of the first battlefield model.

### Deployment zones

* **When** deployment zones are represented, **the system shall** assign zones by battlefield side.
* **When** the player-controlled side is represented, **the system shall** place that side's deployment zone on the left side of the battlefield.
* **When** the enemy side is represented, **the system shall** place that side's deployment zone on the right side of the battlefield.

### Future range operations

* **When** range operations are added after the first battlefield model, **the system shall** support distance between two hexes.
* **When** range operations are added after the first battlefield model, **the system shall** support movement radius from a unit speed value.
* **When** range operations are added after the first battlefield model, **the system shall** support spell area-of-effect rings.
