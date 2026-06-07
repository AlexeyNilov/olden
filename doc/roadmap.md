# Project roadmap

## Status legend

* **Done:** Implemented and verified.
* **Next:** Expected next implementation focus.
* **Later:** Planned but not next.

## Milestone 21: Add more actions

**Status:** Next

* For now stacks can only move or move+attack, but the game provides more options, see `doc/combat_system_reference.md`
* Implement staying out of reach for the melee range action; Should be available by default only for the Attacker because currently in the game NPC(Defender) doesn't do it.
* Make list of available action configurable via .env/our config.py, attacker/defender must have separate config options
* Implement wait and skip actions
* Think carefuly, how can we extend gemon in the simulation with these new actions?

## Future plans

* Later concern: model counterattack capacity as unit combat data, with normal
  melee units defaulting to one counterattack per round, Alert I units allowing
  two counterattacks per round, and Alert II units allowing unlimited
  counterattacks per round.
* Later concern: decide how Guardian Griffin's Loyal Protector passive should
  interact with counterattack capacity, adjacency, and target selection.
* Later concern: decide whether exact initiative and speed ties should alternate
  between attacker and defender by odd/even round, as observed in Olden Era
  reference notes, instead of using stable configured order. Add initiative visualization to the replay app?
