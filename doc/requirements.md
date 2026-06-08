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
* **When** the attacker side is represented, **the system shall** place that side's deployment zone on the left side of the battlefield.
* **When** the defender side is represented, **the system shall** place that side's deployment zone on the right side of the battlefield.

### Battle state

* **When** battle state is represented, **the system shall** keep dynamic unit occupancy separate from field configuration.

### Unit model

* **When** a unit definition is represented, **the system shall** expose stable identity, display name, speed, health, attack, defense, damage range, and attack category data.
* **When** a unit definition has negative speed, **the system shall** reject it as invalid.
* **When** a unit definition has non-positive health, negative attack, negative defense, or an inverted damage range, **the system shall** reject it as invalid.
* **When** a unit stack is represented, **the system shall** expose stack identity, combat side, unit definition, creature count, and current wound damage.
* **When** a unit stack count is zero or negative, **the system shall** reject it as invalid.
* **When** a unit stack's wound damage is negative or greater than or equal to the unit definition's health, **the system shall** reject it as invalid.
* **When** a unit stack is placed on the battlefield, **the system shall** occupy exactly one coordinate.

### Unit catalog

* **When** the packaged unit catalog is loaded, **the system shall** expose unit records by stable unit ID.
* **When** a requested unit ID is missing from a unit catalog, **the system shall** raise a dedicated missing-record exception.
* **When** unit catalog data contains duplicate unit IDs, **the system shall** reject the catalog.
* **When** unit catalog data is loaded, **the system shall** reject malformed required fields before exposing records to callers.
* **When** unit catalog data represents morale or luck, **the system shall** preserve the modifier range as explicit minimum and maximum values.
* **When** unit catalog data contains a modifier range whose maximum is lower than its minimum, **the system shall** reject the catalog.
* **When** a unit record is converted for current combat simulation, **the system shall** produce a unit definition with stable identity, display name, speed, health, attack, defense, damage range, and attack category data.
* **When** a unit record is converted for current combat simulation with an unsupported attack category, **the system shall** reject the conversion.
* **When** bundled unit catalog data is derived from a CC BY-SA source, **the system shall** keep source attribution and catalog license metadata with the packaged data.

### Occupancy

* **When** a unit occupies a coordinate, **the system shall** prevent another unit from occupying the same coordinate at the same time.
* **When** a coordinate is covered by an obstacle, **the system shall** prevent unit occupancy on that coordinate.
* **When** occupancy is queried for a unit, **the system shall** return the coordinate occupied by that unit.
* **When** a unit is removed from occupancy, **the system shall** clear the coordinate occupied by that unit.
* **When** a unit is moved in occupancy, **the system shall** clear its previous coordinate and reserve its destination coordinate.

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

### Melee attack

* **When** a melee attack is resolved, **the system shall** require the attacker and defender to be opposing unit stacks.
* **When** a melee attack is resolved, **the system shall** require the defender to occupy a hex adjacent to the attacker.
* **When** a melee attack is resolved, **the system shall** require the attacker to have a melee-capable attack category.
* **When** a ranged unit is adjacent to an enemy unit stack, **the system shall** allow the ranged unit to perform a melee attack.
* **When** a ranged unit performs a melee attack, **the system shall** reduce the primary attack damage by 50%.
* **When** attack damage is resolved, **the system shall** calculate base damage as attacker count multiplied by the selected damage value from the attacker's damage range.
* **When** attack damage is resolved, **the system shall** apply the attack/defense modifier `(20 + attacker attack) / (20 + defender defense)`.
* **When** attack damage produces a fractional result, **the system shall** round the result down to the nearest integer.
* **When** attack damage is resolved, **the system shall** deal at least `1` final damage.
* **When** attack damage is applied to a unit stack, **the system shall** carry partial damage forward as wound damage on the current surviving creature.
* **When** attack damage kills every creature in a unit stack, **the system shall** remove the defeated stack from battle state and occupancy.
* **When** a melee defender survives an attack and has the melee attack category, **the system shall** immediately counterattack once.
* **When** melee attack resolution is told to suppress counterattacks, **the system shall** resolve only primary attack damage.
* **While** morale, luck, hero stats, damage tags, abilities, and range penalties are deferred, **the system shall** avoid applying those mechanics to melee attack resolution.

### Ranged attack

* **When** a ranged attack is resolved, **the system shall** require the attacker and defender to be opposing unit stacks.
* **When** a ranged attack is resolved, **the system shall** require the attacker to have the ranged attack category.
* **When** a ranged attack is resolved, **the system shall** allow the defender to occupy any battlefield hex that is not adjacent to the attacker.
* **When** a ranged attack is resolved while any living opposing unit stack occupies a hex adjacent to the attacker, **the system shall** reject the ranged attack.
* **When** a ranged attack target is no more than three hexes away, **the system shall** apply no range penalty.
* **When** a ranged attack target is more than three hexes away, **the system shall** reduce damage by 10% per additional hex.
* **When** a ranged attack target is eight or more hexes away, **the system shall** cap the range penalty at 50% damage reduction.
* **When** ranged attack damage produces a fractional result after the range penalty, **the system shall** round the result down to the nearest integer.
* **When** a ranged defender survives an attack, **the system shall** not counterattack.

### Combat simulation

* **When** combat simulation starts, **the system shall** copy the initial battle before moving or attacking with unit stacks.
* **When** combat simulation starts, **the system shall** record a battle-start event in the combat log.
* **When** combat simulation advances rounds, **the system shall** give each non-defeated unit stack one action opportunity per round.
* **When** combat simulation orders unit stacks within a round, **the system shall** act with higher initiative stacks before lower initiative stacks.
* **When** combat simulation orders unit stacks with equal initiative, **the system shall** use higher speed as the tie-breaker.
* **When** combat simulation orders unit stacks with equal initiative and speed, **the system shall** preserve configured stack order.
* **When** combat simulation selects a target for the acting unit stack by default, **the system shall** target the living opposing stack with the highest estimated threat removed by the acting stack's average-damage attack.
* **When** combat simulation estimates threat removed for target selection, **the system shall** multiply the number of target creatures the acting stack can kill by the target stack's average per-creature damage against the acting stack.
* **When** combat simulation selects a target with the nearest-opponent policy, **the system shall** target the nearest living opposing stack.
* **When** combat simulation target selection has equal scores for multiple living opposing stacks, **the system shall** choose the nearest stack.
* **When** combat simulation target selection has multiple living opposing stacks with equal scores and equal distance, **the system shall** preserve configured stack order.
* **When** combat simulation selects an action for a unit stack, **the system shall** consider only actions configured for that stack's combat side.
* **When** no configured action is applicable for a unit stack during combat simulation, **the system shall** raise an action-selection error.
* **When** the acting unit stack is not adjacent to its opponent, **the system shall** move toward a passable engagement hex adjacent to the opponent.
* **When** multiple equally short engagement paths are available, **the system shall** choose randomly among those paths.
* **When** a simulated movement path is longer than the acting unit stack's speed, **the system shall** move only as far along that path as the stack's speed allows.
* **When** the acting unit stack is adjacent to its opponent, **the system shall** perform a melee attack.
* **When** combat simulation movement brings the acting unit stack adjacent to its target, **the system shall** perform the melee attack in the same action opportunity.
* **When** a configured ranged attack action is selected, **the system shall** perform a ranged attack against the selected opponent without movement.
* **When** a configured ranged attack action is considered while any enemy is adjacent to the acting unit stack, **the system shall** not make the ranged attack action applicable.
* **When** a configured stay-out-of-melee-reach action is selected, **the system shall** move the acting unit stack toward a selected opponent only to a reachable hex that is outside that opponent's next melee engagement reach.
* **When** a unit stack waits during combat simulation, **the system shall** move that stack's action to the end of the current round without counting the wait itself as a completed action opportunity.
* **When** multiple unit stacks wait in the same round, **the system shall** resolve their delayed actions in flipped initiative order, with lower-initiative stacks acting before higher-initiative stacks.
* **When** a unit stack has already waited during the current round, **the system shall** prevent that stack from waiting again during that round.
* **When** a unit stack skips during combat simulation, **the system shall** end that stack's current action opportunity without movement or attack and count the skip as a completed action opportunity.
* **When** combat simulation resolves counterattacks, **the system shall** allow each defending unit stack to counterattack at most once per round.
* **When** combat simulation records movement, **the system shall** use combat-log movement events that can be replayed from the original battle.
* **When** combat simulation records an attack, **the system shall** use a combat-log attack event that can be replayed from the original battle.
* **When** combat simulation records a wait or skip, **the system shall** use combat-log events that can be replayed from the original battle.
* **When** one side has no living unit stacks, **the system shall** stop combat simulation.
* **While** morale, luck, target selection beyond configured target policy, and multi-stack battle strategy are deferred, **the system shall** avoid applying those mechanics to combat simulation.
* **When** the demo combat simulation sample runs, **the system shall** load battle initial state from `data/demo_battle.yaml` and save the combat log in the `data` folder.

### Strategy discovery

* **When** stack-split strategy discovery evaluates a genome, **the system shall** map each genome slot to a fixed attacker deployment coordinate and create one attacker unit stack for each non-empty slot.
* **When** stack-split strategy discovery evaluates a genome, **the system shall** require the genome to contain no more than seven slots, no negative stack counts, and exactly the configured attacker unit pool size.
* **When** stack-split strategy discovery configures deployment slots, **the system shall** reject slots occupied by base-battle stacks other than the attacker pool stack.
* **When** stack-split strategy discovery evaluates a strategy, **the system shall** use the strategy's wait policy to choose whether attacker unit stacks wait instead of using the default combat action order.
* **When** a stack-split strategy uses the first-action-if-safe wait policy, **the system shall** wait with an attacker unit stack on its first round action only while the stack is outside the selected opponent's next melee engagement reach.
* **When** stack-split strategy discovery scores a genome, **the system shall** use average unit damage so repeated evaluations of the same genome are deterministic.
* **When** stack-split strategy discovery encounters the same genome more than once in one discovery run, **the system shall** reuse its deterministic evaluation.
* **When** stack-split strategy discovery evaluates a population with multiple workers, **the system shall** preserve the same population order, selection behavior, and best result as serial evaluation for the same random seed.
* **When** stack-split strategy discovery scores a completed combat simulation, **the system shall** prioritize defender units killed, then surviving attacker units, then remaining attacker health, and then faster completion.
* **When** stack-split strategy discovery evaluates a scenario without an explicit turn cap, **the system shall** simulate at most 100 action opportunities.
* **When** the genetic strategy discovery sample reads configuration, **the system shall** allow `GENETIC_STRATEGY_DISCOVERY_MAX_TURNS` to override the stack-split scenario turn cap.
* **When** the genetic strategy discovery sample reads configuration, **the system shall** allow `GENETIC_STRATEGY_DISCOVERY_MUTATION_RATE` from `0` through `1` to override the stack-split mutation rate.
* **When** the genetic strategy discovery sample builds a stack-split scenario, **the system shall** exclude default attacker deployment slots occupied by non-pool stacks in the loaded battle.
* **When** the genetic strategy discovery sample completes, **the system shall** save the best discovered initial battle and a replayable combat log for that battle.
* **While** turn-level combat strategy is deferred, **the system shall** keep stack-split strategy discovery limited to initial army formation and fixed deployment slots.

### Combat log

* **When** a battle-start event is recorded, **the system shall** assign it the next contiguous combat-log sequence number.
* **When** a unit-moved event is recorded, **the system shall** include the next contiguous sequence number, turn marker, stack ID, start coordinate, destination coordinate, and movement path.
* **When** a unit-attacked event is recorded, **the system shall** include the next contiguous sequence number, turn marker, attacker ID, defender ID, primary attack damage result, and optional counterattack damage result.
* **When** a unit-waited event is recorded, **the system shall** include the next contiguous sequence number, turn marker, and stack ID.
* **When** a unit-skipped event is recorded, **the system shall** include the next contiguous sequence number, turn marker, and stack ID.
* **When** a combat log is saved to a file, **the system shall** write YAML that can be loaded back into an equivalent combat log.
* **When** a combat log is loaded from YAML, **the system shall** reject unsupported schema versions instead of migrating older log formats.
* **When** a combat log is loaded from YAML, **the system shall** reject event sequences that are not contiguous from `1`.
* **When** a combat log is replayed from a battle initial state, **the system shall** apply recorded unit movement and attack events in sequence to reconstruct final battle state.
* **When** combat-log replay tools consume logs, **the system shall** treat them as current-development artifacts generated by the current Olden codebase.
* **When** a combat log movement event does not match movement that can be replayed from current battle state, **the system shall** reject replay.
* **When** a combat log attack event does not match attack damage that can be replayed from current battle state, **the system shall** reject replay.

### Combat replay

* **When** combat replay frames are built, **the system shall** include an initial-state frame before movement events are applied.
* **When** combat replay frames are built, **the system shall** include one frame for each replayed unit-moved or unit-attacked event.
* **When** combat replay frames are built, **the system shall** preserve the combat-log event associated with each non-initial frame.
* **When** combat replay frames are built, **the system shall** reject movement events that do not replay from the current frame state.
* **When** the combat replay view is launched, **the system shall** load `data/demo_battle.yaml` and `data/demo_combat_log.yaml` by default.
* **When** the combat replay view is shown, **the system shall** render one battlefield state per replay frame.
* **When** the combat replay view is shown, **the system shall** show a combat-log panel to the right of the battlefield on desktop layouts.
* **When** the combat replay view shows combat-log entries, **the system shall** list the initial state, movement events, and attack events in replay order.
* **When** the combat replay view shows the combat-log panel, **the system shall** make the panel scrollable.
* **When** the combat replay view shows the current replay frame, **the system shall** visually mark the matching combat-log entry.
* **When** the combat replay view describes a movement event, **the system shall** include the moving stack, start coordinate, and destination coordinate.
* **When** the combat replay view describes an attack event, **the system shall** include the attacker, defender, final damage, killed creatures, defender count after damage, and counterattack details when present.
* **When** the combat replay view advances playback, **the system shall** wait for the configured delay before showing the next frame.
* **When** the combat replay view delay is changed, **the system shall** apply the new delay to subsequent automatic frame advances.
* **When** the combat replay view reaches the final frame, **the system shall** stop automatic playback.

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
* **When** a unit stack is rendered with stack metadata, **the system shall** display a visible combat-side marker for the stack.
* **When** the combat replay view is launched, **the system shall** load the Swordsman unit definition from the packaged unit catalog record with ID `esquire`.

### Deferred behavior

* **While** range and movement math remains pure geometric math, **the system shall** avoid exposing pathfinding APIs from range operations.
* **While** attacker/defender tie alternation and army-slot ordering are deferred, **the system shall** preserve configured stack order for exact initiative and speed ties.
* **While** combat action simulation beyond melee and ranged attacks is deferred, **the system shall** avoid exposing morale, luck, ability, cost, growth, upgrade, long-reach attack, or other deferred behavior as part of the Unit model.
* **While** combat mechanics beyond committed turn ordering, melee attack behavior, and ranged attack behavior are deferred, **the system shall** avoid applying morale, luck, economy, upgrade, ability, long-reach attack, or other deferred behavior from unit catalog records.
* **While** line-of-sight and spell area-of-effect rings are deferred, **the system shall** avoid exposing line-of-sight or spell area-of-effect APIs as part of range and movement math.
* **While** all unit stacks occupy exactly one coordinate, **the system shall** avoid exposing multi-hex pathfinding or footprint-clearance behavior.
* **While** terrain effects and special movement are deferred, **the system shall** avoid exposing terrain-specific costs, flying, teleporting, attack zones, turn order, waiting, or action-economy behavior as part of movement simulation.
