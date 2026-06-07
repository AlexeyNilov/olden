# Project roadmap

## Status legend

* **Done:** Implemented and verified.
* **Next:** Expected next implementation focus.
* **Later:** Planned but not next.

## Milestone 20: Better targeting

**Status:** Later

* Replace nearest-opponent target selection with explicit combat strategy
* Proposal: the optimal targeting is removing the most dangerous units from the field; dangerous means potentially applicabale damage; the math should include number of units the current stack can potentialy kill using its average damage; tie breaks could be solved by the nearest stack, and stack with zero counterattack count; in other cases the targeting could be just random;

## Future plans

* Implement staying out of melee range action; Attacker only? How to add it into the genom?
* Implement wait and skip actions; how to add them into the genom?

* Later concern: model counterattack capacity as unit combat data, with normal
  melee units defaulting to one counterattack per round, Alert I units allowing
  two counterattacks per round, and Alert II units allowing unlimited
  counterattacks per round.
* Later concern: decide how Guardian Griffin's Loyal Protector passive should
  interact with counterattack capacity, adjacency, and target selection.
* Later concern: decide whether exact initiative and speed ties should alternate
  between attacker and defender by odd/even round, as observed in Olden Era
  reference notes, instead of using stable configured order. Add initiative visualization to the replay app?
