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

### Field configuration

* **When** field configuration is represented, **the system shall** keep deployment-zone data separate from dynamic unit occupancy.
* **When** obstacles are represented, **the system shall** support obstacles that cover one or more hex coordinates.
* **When** obstacles are represented, **the system shall** treat each obstacle coordinate as a whole-hex blocker.

### Deployment zones

* **When** deployment zones are represented, **the system shall** assign zones by battlefield side.
* **When** the player-controlled side is represented, **the system shall** place that side's deployment zone on the left side of the battlefield.
* **When** the enemy side is represented, **the system shall** place that side's deployment zone on the right side of the battlefield.

### Battle state

* **When** battle state is represented, **the system shall** keep dynamic unit occupancy separate from field configuration.

### Unit model

* **When** a unit definition is represented, **the system shall** expose stable identity, display name, speed, and footprint data.
* **When** a unit definition has negative speed, **the system shall** reject it as invalid.
* **When** a unit stack is represented, **the system shall** expose stack identity, combat side, unit definition, and creature count.
* **When** a unit stack count is zero or negative, **the system shall** reject it as invalid.
* **When** a single-hex unit footprint is anchored at a coordinate, **the system shall** occupy only the anchor coordinate.
* **When** a multi-hex unit footprint is anchored at a coordinate, **the system shall** derive occupied coordinates from the anchor and footprint offsets.
* **When** a unit footprint is empty or omits the anchor offset, **the system shall** reject it as invalid.

### Occupancy

* **When** a unit occupies a coordinate, **the system shall** prevent another unit from occupying the same coordinate at the same time.
* **When** a coordinate is covered by an obstacle, **the system shall** prevent unit occupancy on that coordinate.
* **When** a unit footprint covers multiple coordinates, **the system shall** prevent unit occupancy if any covered coordinate is already occupied.
* **When** a unit footprint covers multiple coordinates, **the system shall** prevent unit occupancy if any covered coordinate is blocked by an obstacle.

### Range and movement math

* **When** distance is calculated from a coordinate to itself, **the system shall** return `0`.
* **When** distance is calculated between adjacent valid coordinates, **the system shall** return `1`.
* **When** distance is calculated between two valid coordinates, **the system shall** return the same value regardless of coordinate order.
* **When** distance is calculated with an invalid start or end coordinate, **the system shall** reject the request before calculating distance.
* **When** movement radius is calculated with speed `0`, **the system shall** return only the origin coordinate.
* **When** movement radius is calculated with positive speed, **the system shall** return every valid battlefield coordinate within that hex distance from the origin.
* **When** movement radius is calculated near a battlefield edge, **the system shall** exclude coordinates outside the battlefield.
* **When** movement radius is calculated with negative speed, **the system shall** reject the request.

### Deferred behavior

* **While** pathfinding is deferred, **the system shall** avoid exposing pathfinding APIs as part of range and movement math.
* **While** turn-order simulation is deferred, **the system shall** avoid exposing initiative tie-breaker behavior.
* **While** combat action simulation is deferred, **the system shall** avoid exposing damage, morale, luck, attack-resolution, ability, cost, growth, or upgrade behavior as part of the Unit model.
* **While** line-of-sight and spell area-of-effect rings are deferred, **the system shall** avoid exposing line-of-sight or spell area-of-effect APIs as part of range and movement math.
* **While** movement simulation is deferred, **the system shall** keep movement radius independent of obstacles and dynamic occupancy.
