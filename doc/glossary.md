# Glossary

* **Battle:** A running combat instance. Future battle state includes units, turns, actions, effects, and mutable combat state.
* **Battle initial state:** Serialized setup data used to create a battle before combat-log events are applied.
* **Battle state:** Dynamic combat data such as unit occupancy.
* **Battlefield:** The static combat field made of pointy-top hexes arranged in staggered rows.
* **Battlefield hex:** One addressable hex on the battlefield, including its coordinate and static field metadata.
* **Battlefield topology:** The battlefield's shape, valid coordinates, and neighbor relationships.
* **Battlefield view:** A read-only visualization of battlefield topology, field configuration, and battle-state occupancy.
* **Attack category:** Future unit attack classification, such as melee, long-reach, or ranged.
* **Combat:** The bounded context for battlefield, unit, movement, action, spell, and battle-state rules.
* **Combat side:** One of the opposing sides in combat. The player-controlled side starts on the left; the enemy side starts on the right.
* **Combat log:** Ordered combat-event history that can be replayed from a battle initial state.
* **Combat log event:** One recorded battle event with a stable sequence number and event-specific payload.
* **Combat replay frame:** One renderable battle state in a combat-log replay, optionally associated with the event that produced it.
* **Combat replay view:** A local browser view that steps through combat replay frames with configurable playback delay.
* **Deployment zone:** The side-based set of coordinates where units can start combat.
* **Engagement hex:** A passable hex adjacent to an opposing unit stack that a movement-only simulation can move toward before combat actions exist.
* **Field configuration:** Static battlefield data such as obstacles and deployment zones.
* **Hex coordinate:** A zero-based `(column, row)` address for one battlefield hex.
* **Initiative:** Future unit stat that contributes to turn order.
* **Luck:** Future combat modifier that can alter damage up or down during attack resolution.
* **Morale:** Future combat modifier that can grant an extra action or cause a lost action.
* **Movement cost:** The number of movement points needed to traverse one step in a movement path. Current single-hex movement cost is always `1` per step.
* **Movement path:** An ordered sequence of battlefield coordinates from a start coordinate to a destination coordinate.
* **Movement-only simulation:** A limited battle simulation that alternates movement between two unit stacks until they become adjacent, without initiative or combat actions.
* **Movement radius:** The set of valid battlefield coordinates within a unit's speed distance from an origin, ignoring obstacles, occupancy, and pathfinding.
* **Modifier range:** A minimum and maximum value for a future combat modifier such as morale or luck.
* **Obstacle:** A whole-hex blocker covering one or more battlefield coordinates.
* **Obstacle map:** The field configuration that answers whether a coordinate is blocked by an obstacle.
* **Occupancy:** The dynamic mapping of units to battlefield coordinates.
* **Passable coordinate:** A valid battlefield coordinate that is not blocked by an obstacle and is not occupied by another unit during movement pathfinding.
* **Range operation:** Hex-math behavior such as distance between hexes or movement radius by unit speed.
* **Renderable hex:** Battlefield-view data for one valid hex coordinate, including display position and visual state.
* **Round:** A future combat cycle in which unit stacks normally act once. Current combat logs store round numbers as replay metadata only.
* **Unreachable path:** A movement request where no passable path exists from the start coordinate to the destination coordinate.
* **Turn:** A future unit-stack action opportunity within a round. Current combat logs store turn numbers as replay metadata only.
* **Turn marker:** Replay metadata identifying the round and turn number associated with a logged event.
* **Unit catalog:** A local collection of static unit records loaded from packaged data.
* **Unit definition:** Static unit data shared by every stack of that unit type.
* **Unit footprint:** The set of battlefield coordinates occupied by a unit stack when anchored at a coordinate.
* **Unit image:** A battlefield-view visual asset for a unit definition, resolved by stable unit ID.
* **Unit record:** A catalog entry for one unit type, including source metadata and stats that may not yet affect combat simulation.
* **Unit stack:** A battle-state instance of a unit definition with a side and creature count.
