# Glossary

* **Battle:** A running combat instance. Future battle state includes units, turns, actions, effects, and mutable combat state.
* **Battle state:** Dynamic combat data such as unit occupancy.
* **Battlefield:** The static combat field made of flat-top hexes arranged in staggered rows.
* **Battlefield hex:** One addressable hex on the battlefield, including its coordinate and static field metadata.
* **Battlefield topology:** The battlefield's shape, valid coordinates, and neighbor relationships.
* **Attack category:** Future unit attack classification, such as melee, long-reach, or ranged.
* **Combat:** The bounded context for battlefield, unit, movement, action, spell, and battle-state rules.
* **Combat side:** One of the opposing sides in combat. The player-controlled side starts on the left; the enemy side starts on the right.
* **Deployment zone:** The side-based set of coordinates where units can start combat.
* **Field configuration:** Static battlefield data such as obstacles and deployment zones.
* **Hex coordinate:** A zero-based `(column, row)` address for one battlefield hex.
* **Initiative:** Future unit stat that contributes to turn order.
* **Luck:** Future combat modifier that can alter damage up or down during attack resolution.
* **Morale:** Future combat modifier that can grant an extra action or cause a lost action.
* **Obstacle:** A whole-hex blocker covering one or more battlefield coordinates.
* **Obstacle map:** The field configuration that answers whether a coordinate is blocked by an obstacle.
* **Occupancy:** The dynamic mapping of units to battlefield coordinates.
* **Range operation:** Hex-math behavior such as distance between hexes, movement radius by unit speed, or spell area-of-effect rings.
* **Unit definition:** Static unit data shared by every stack of that unit type.
* **Unit footprint:** The set of battlefield coordinates occupied by a unit stack when anchored at a coordinate.
* **Unit stack:** A battle-state instance of a unit definition with a side and creature count.
