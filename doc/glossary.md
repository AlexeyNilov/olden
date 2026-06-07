# Glossary

* **Battle:** A running combat instance. Future battle state includes units, turns, actions, effects, and mutable combat state.
* **Battle initial state:** Serialized setup data used to create a battle before combat-log events are applied.
* **Battle state:** Dynamic combat data such as unit occupancy.
* **Battlefield:** The static combat field made of pointy-top hexes arranged in staggered rows.
* **Battlefield hex:** One addressable hex on the battlefield, including its coordinate and static field metadata.
* **Battlefield topology:** The battlefield's shape, valid coordinates, and neighbor relationships.
* **Battlefield view:** A read-only visualization of battlefield topology, field configuration, and battle-state occupancy.
* **Attack category:** Unit attack classification. Current combat simulation supports melee; long-reach and ranged attacks are deferred.
* **Combat:** The bounded context for battlefield, unit, movement, action, spell, and battle-state rules.
* **Combat side:** One of the opposing sides in combat. The attacker side starts on the left; the defender side starts on the right.
* **Combat log:** Ordered combat-event history that can be replayed from a battle initial state.
* **Combat log event:** One recorded battle event with a stable sequence number and event-specific payload.
* **Combat replay frame:** One renderable battle state in a combat-log replay, optionally associated with the event that produced it.
* **Combat replay view:** A local browser view that steps through combat replay frames with configurable playback delay.
* **Combat simulation:** A limited battle simulation that orders unit-stack action opportunities, moves stacks toward selected opponents, and resolves melee attacks until one side is defeated or simulation stops.
* **Combat action:** A configured simulation choice available to a unit stack, such as melee engagement, staying out of melee reach, waiting, or skipping.
* **Deployment zone:** The side-based set of coordinates where units can start combat.
* **Engagement hex:** A passable hex adjacent to an opposing unit stack that combat simulation can move toward before resolving melee attacks.
* **Field configuration:** Static battlefield data such as obstacles and deployment zones.
* **Hex coordinate:** A zero-based `(column, row)` address for one battlefield hex.
* **Initiative:** Unit stat that determines combat simulation turn order before speed and configured stack order tie-breakers.
* **Luck:** Future combat modifier that can alter damage up or down during attack resolution.
* **Morale:** Future combat modifier that can grant an extra action or cause a lost action.
* **Movement cost:** The number of movement points needed to traverse one step in a movement path. Current single-hex movement cost is always `1` per step.
* **Movement path:** An ordered sequence of battlefield coordinates from a start coordinate to a destination coordinate.
* **Movement radius:** The set of valid battlefield coordinates within a unit's speed distance from an origin, ignoring obstacles, occupancy, and pathfinding.
* **Modifier range:** A minimum and maximum value for a future combat modifier such as morale or luck.
* **Obstacle:** A whole-hex blocker covering one or more battlefield coordinates.
* **Obstacle map:** The field configuration that answers whether a coordinate is blocked by an obstacle.
* **Occupancy:** The dynamic mapping of units to battlefield coordinates.
* **Passable coordinate:** A valid battlefield coordinate that is not blocked by an obstacle and is not occupied by another unit during movement pathfinding.
* **Range operation:** Hex-math behavior such as distance between hexes or movement radius by unit speed.
* **Renderable hex:** Battlefield-view data for one valid hex coordinate, including display position and visual state.
* **Round:** A future combat cycle in which unit stacks normally act once. Current combat logs store round numbers as replay metadata only.
* **Skip:** A combat action that ends a unit stack's current action opportunity without movement or attack.
* **Stay out of melee reach:** A combat action that moves a unit stack toward an opponent while keeping the destination outside that opponent's next melee engagement reach.
* **Unreachable path:** A movement request where no passable path exists from the start coordinate to the destination coordinate.
* **Turn:** A future unit-stack action opportunity within a round. Current combat logs store turn numbers as replay metadata only.
* **Turn marker:** Replay metadata identifying the round and turn number associated with a logged event.
* **Unit catalog:** A local collection of static unit records loaded from packaged data.
* **Unit definition:** Static unit data shared by every stack of that unit type.
* **Unit image:** A battlefield-view visual asset for a unit definition, resolved by stable unit ID.
* **Unit record:** A catalog entry for one unit type, including source metadata and stats that may not yet affect combat simulation.
* **Unit stack:** A battle-state instance of a unit definition with a side and creature count.
* **Unit-attacked event:** A combat-log event recording one melee attack action, including primary attack damage and optional counterattack damage.
* **Unit-skipped event:** A combat-log event recording that a unit stack skipped its action opportunity.
* **Unit-waited event:** A combat-log event recording that a unit stack delayed its action to the end of the current round.
* **Wait:** A combat action that delays a unit stack's action until the end of the current round without consuming that stack's completed action opportunity.
* **Wound damage:** Damage already applied to the current surviving creature in a unit stack, carried forward between attacks until that creature dies.
