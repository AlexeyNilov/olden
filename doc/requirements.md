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
* **When** the battlefield topology is represented, **the system shall** model pointy-top hexes with staggered odd-numbered rows.

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

### Unit catalog

* **When** the packaged unit catalog is loaded, **the system shall** expose unit records by stable unit ID.
* **When** a requested unit ID is missing from a unit catalog, **the system shall** raise a dedicated missing-record exception.
* **When** unit catalog data contains duplicate unit IDs, **the system shall** reject the catalog.
* **When** unit catalog data is loaded, **the system shall** reject malformed required fields before exposing records to callers.
* **When** unit catalog data represents morale or luck, **the system shall** preserve the modifier range as explicit minimum and maximum values.
* **When** unit catalog data contains a modifier range whose maximum is lower than its minimum, **the system shall** reject the catalog.
* **When** a unit record is converted for current combat simulation, **the system shall** produce a unit definition from only stable identity, display name, speed, and single-hex footprint data.
* **When** bundled unit catalog data is derived from a CC BY-SA source, **the system shall** keep source attribution and catalog license metadata with the packaged data.

### Occupancy

* **When** a unit occupies a coordinate, **the system shall** prevent another unit from occupying the same coordinate at the same time.
* **When** a coordinate is covered by an obstacle, **the system shall** prevent unit occupancy on that coordinate.
* **When** a unit footprint covers multiple coordinates, **the system shall** prevent unit occupancy if any covered coordinate is already occupied.
* **When** a unit footprint covers multiple coordinates, **the system shall** prevent unit occupancy if any covered coordinate is blocked by an obstacle.
* **When** occupancy is queried for a unit, **the system shall** return every coordinate occupied by that unit.
* **When** a unit is removed from occupancy, **the system shall** clear every coordinate occupied by that unit.
* **When** a single-hex unit is moved in occupancy, **the system shall** clear its previous coordinate and reserve its destination coordinate.

### Battle initial state

* **When** battle initial state is loaded from YAML, **the system shall** build a battle from battlefield obstacles, unit stacks, combat sides, stack counts, and starting anchors.
* **When** battle initial state is loaded from YAML, **the system shall** resolve unit definitions through the unit catalog by stable unit ID.
* **When** battle initial state contains duplicate stack IDs, **the system shall** reject the setup before exposing the battle.
* **When** battle initial state places a stack on a blocked coordinate, **the system shall** reject the setup before exposing the battle.
* **When** battle initial state places overlapping stacks, **the system shall** reject the setup before exposing the battle.
* **When** battle initial state is saved to a file, **the system shall** write YAML that can be loaded back into an equivalent battle setup.

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

### Battle movement

* **When** a battle moves a unit stack, **the system shall** validate the movement against the stack's current anchor, unit speed, obstacles, and occupancy before mutating occupancy.
* **When** a battle moves a unit stack, **the system shall** return a movement result containing the stack ID, start coordinate, destination coordinate, and movement path.

### Movement-only simulation

* **When** movement-only simulation starts, **the system shall** copy the initial battle before moving unit stacks.
* **When** movement-only simulation starts, **the system shall** record a battle-start event in the combat log.
* **When** movement-only simulation runs without initiative, **the system shall** move the configured first stack before the configured second stack.
* **When** movement-only simulation advances turns, **the system shall** alternate between the two configured unit stacks.
* **When** a simulated unit stack is not adjacent to its opponent, **the system shall** move toward a passable engagement hex adjacent to the opponent.
* **When** multiple equally short engagement paths are available, **the system shall** choose randomly among those paths.
* **When** a simulated movement path is longer than the acting unit stack's speed, **the system shall** move only as far along that path as the stack's speed allows.
* **When** simulated unit stacks are adjacent, **the system shall** stop before adding combat actions.
* **When** movement-only simulation records movement, **the system shall** use combat-log movement events that can be replayed from the original battle.

### Combat log

* **When** a battle-start event is recorded, **the system shall** assign it the next contiguous combat-log sequence number.
* **When** a unit-moved event is recorded, **the system shall** include the next contiguous sequence number, turn marker, stack ID, start coordinate, destination coordinate, and movement path.
* **When** a combat log is saved to a file, **the system shall** write YAML that can be loaded back into an equivalent combat log.
* **When** a combat log is loaded from YAML, **the system shall** reject event sequences that are not contiguous from `1`.
* **When** a combat log is replayed from a battle initial state, **the system shall** apply recorded unit movement events in sequence to reconstruct final occupancy.
* **When** a combat log movement event does not match movement that can be replayed from current battle state, **the system shall** reject replay.

### Battlefield view

* **When** battlefield view data is produced, **the system shall** include one renderable hex for every valid battlefield coordinate.
* **When** battlefield view layout is produced, **the system shall** preserve pointy-top odd-row staggering.
* **When** battlefield view layout is produced, **the system shall** align neighboring hexes by shared sides without overlap or gaps.
* **When** battlefield view data is produced, **the system shall** expose deployment-zone state for each renderable hex.
* **When** battlefield view data is produced for blocked coordinates, **the system shall** expose blocked state for those renderable hexes.
* **When** battlefield view data is produced for occupied coordinates, **the system shall** expose the occupying unit identity for those renderable hexes.
* **When** battlefield view data is produced, **the system shall** not mutate battlefield topology, field configuration, or occupancy.
* **When** a unit stack is rendered with an existing unit image matching its unit definition ID, **the system shall** display the unit image on the occupied hex.
* **When** a unit stack is rendered with an existing unit image, **the system shall** display only the stack count as the unit label.
* **When** a unit stack is rendered without an existing unit image, **the system shall** display fallback text using the unit name and stack count.
* **When** the demo battlefield view is launched, **the system shall** load the Swordsman unit definition from the packaged unit catalog record with ID `esquire`.

### Deferred behavior

* **While** range and movement math remains pure geometric math, **the system shall** avoid exposing pathfinding APIs from range operations.
* **While** turn-order simulation is deferred, **the system shall** avoid exposing initiative tie-breaker behavior.
* **While** combat action simulation is deferred, **the system shall** avoid exposing damage, morale, luck, attack-resolution, ability, cost, growth, or upgrade behavior as part of the Unit model.
* **While** combat actions are deferred, **the system shall** avoid applying attack, defense, damage, morale, luck, initiative, economy, upgrade, or ability behavior from unit catalog records.
* **While** line-of-sight and spell area-of-effect rings are deferred, **the system shall** avoid exposing line-of-sight or spell area-of-effect APIs as part of range and movement math.
* **While** multi-hex movement is deferred, **the system shall** avoid exposing multi-hex pathfinding or footprint-clearance behavior as part of single-hex movement simulation.
* **While** terrain effects and special movement are deferred, **the system shall** avoid exposing terrain-specific costs, flying, teleporting, attack zones, turn order, waiting, or action-economy behavior as part of movement simulation.
