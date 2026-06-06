# Glossary

* **Battle:** A running combat instance. Future battle state includes units, turns, actions, effects, and mutable combat state.
* **Battle state:** Dynamic combat data such as unit occupancy.
* **Battlefield:** The static combat field made of flat-top hexes arranged in staggered rows.
* **Battlefield topology:** The battlefield's shape, valid coordinates, and neighbor relationships.
* **Combat:** The bounded context for battlefield, unit, movement, action, spell, and battle-state rules.
* **Deployment side:** One of the opposing combat sides. The player-controlled side starts on the left; the enemy side starts on the right.
* **Deployment zone:** The side-based set of coordinates where units can start combat.
* **Field configuration:** Static battlefield data such as obstacles and deployment zones.
* **Hex coordinate:** A zero-based `(column, row)` address for one battlefield hex.
* **Obstacle:** A whole-hex blocker covering one or more battlefield coordinates.
* **Occupancy:** The dynamic mapping of units to battlefield coordinates.
* **Range operation:** Hex-math behavior such as distance between hexes, movement radius by unit speed, or spell area-of-effect rings.
