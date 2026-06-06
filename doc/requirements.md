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
* **When** occupancy is queried for a unit, **the system shall** return every coordinate occupied by that unit.
* **When** a unit is removed from occupancy, **the system shall** clear every coordinate occupied by that unit.
* **When** a single-hex unit is moved in occupancy, **the system shall** clear its previous coordinate and reserve its destination coordinate.

### Range and movement math

* **When** distance is calculated from a coordinate to itself, **the system shall** return `0`.
* **When** distance is calculated between adjacent valid coordinates, **the system shall** return `1`.
* **When** distance is calculated between two valid coordinates, **the system shall** return the same value regardless of coordinate order.
* **When** distance is calculated with an invalid start or end coordinate, **the system shall** reject the request before calculating distance.
* **When** movement radius is calculated with speed `0`, **the system shall** return only the origin coordinate.
* **When** movement radius is calculated with positive speed, **the system shall** return every valid battlefield coordinate within that hex distance from the origin.
* **When** movement radius is calculated near a battlefield edge, **the system shall** exclude coordinates outside the battlefield.
* **When** movement radius is calculated with negative speed, **the system shall** reject the request.

### Movement simulation

* **When** a path is found for single-hex movement, **the system shall** return the shortest path as ordered anchor coordinates including the start and destination.
* **When** a movement path is calculated, **the system shall** treat each step between adjacent coordinates as cost `1`.
* **When** single-hex movement is pathfinding, **the system shall** treat obstacle coordinates as impassable.
* **When** single-hex movement is pathfinding, **the system shall** treat coordinates occupied by other units as impassable.
* **When** single-hex movement is pathfinding, **the system shall** allow the moving unit's own current coordinate.
* **When** a destination cannot be reached, **the system shall** raise a dedicated unreachable-path exception.
* **When** movement is validated within unit speed, **the system shall** return the valid movement path without mutating occupancy.
* **When** movement is validated beyond unit speed, **the system shall** reject the movement.
* **When** movement is validated with an invalid start or destination coordinate, **the system shall** reject the movement.
* **When** movement is validated to a blocked or other-unit-occupied destination, **the system shall** reject the movement.

### Battlefield view

* **When** battlefield view data is produced, **the system shall** include one renderable hex for every valid battlefield coordinate.
* **When** battlefield view layout is produced, **the system shall** preserve flat-top odd-row staggering.
* **When** battlefield view data is produced, **the system shall** expose deployment-zone state for each renderable hex.
* **When** battlefield view data is produced for blocked coordinates, **the system shall** expose blocked state for those renderable hexes.
* **When** battlefield view data is produced for occupied coordinates, **the system shall** expose the occupying unit identity for those renderable hexes.
* **When** battlefield view data is produced, **the system shall** not mutate battlefield topology, field configuration, or occupancy.

### Deferred behavior

* **While** range and movement math remains pure geometric math, **the system shall** avoid exposing pathfinding APIs from range operations.
* **While** turn-order simulation is deferred, **the system shall** avoid exposing initiative tie-breaker behavior.
* **While** combat action simulation is deferred, **the system shall** avoid exposing damage, morale, luck, attack-resolution, ability, cost, growth, or upgrade behavior as part of the Unit model.
* **While** line-of-sight and spell area-of-effect rings are deferred, **the system shall** avoid exposing line-of-sight or spell area-of-effect APIs as part of range and movement math.
* **While** multi-hex movement is deferred, **the system shall** avoid exposing multi-hex pathfinding or footprint-clearance behavior as part of single-hex movement simulation.
* **While** terrain effects and special movement are deferred, **the system shall** avoid exposing terrain-specific costs, flying, teleporting, attack zones, turn order, waiting, or action-economy behavior as part of movement simulation.
