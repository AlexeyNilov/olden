# Project roadmap

## Status legend

* **Done:** Implemented and verified.
* **Next:** Expected next implementation focus.
* **Later:** Planned but not next.

## Milestone 23: Add Hero

**Status:** Done

Implemented first hero slice:

* Armies can optionally include a catalog-backed hero through `hero_id`.
* Hero data includes stable ID, display name, level, experience, attack, defense,
  spell power, and knowledge.
* Army YAML can load and save optional hero IDs while existing hero-less armies
  remain valid.
* Packaged hero catalog includes John Johnson with source attribution.
* Current summaries preserve hero data but do not apply hero stat effects to
  army totals or combat simulation.


## Future plans

* Later concern: add defense-aware and simulation-backed army matchup
  predictions.
* Later concern: define hero leveling thresholds, stat-growth rules, skills,
  spells, and ability unlocks.
* Later concern: resolve and encode hero starting armies once source image
  labels can be verified reliably.
* Later concern: apply committed hero attack and defense effects to combat
  damage once hero stat effects are promoted to requirements.
* Later concern: model counterattack capacity as unit combat data, with normal
  melee units defaulting to one counterattack per round, Alert I units allowing
  two counterattacks per round, and Alert II units allowing unlimited
  counterattacks per round.
* Later concern: decide how Guardian Griffin's Loyal Protector passive should
  interact with counterattack capacity, adjacency, and target selection.
* Later concern: decide whether exact initiative and speed ties should alternate
  between attacker and defender by odd/even round, as observed in Olden Era
  reference notes, instead of using stable configured order. 
* Add initiative visualization to the replay app?
