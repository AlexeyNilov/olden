# Project roadmap

## Status legend

* **Done:** Implemented and verified.
* **Next:** Expected next implementation focus.
* **Later:** Planned but not next.

## Milestone 17: Combat simulation responsibility split

**Status:** Later

* Review `src/olden/combat/combat_simulation.py` responsibilities before adding more combat mechanics.
* Keep combat simulation responsible for advancing the simulation, not for owning every policy and rule detail.
* Separate round and action-opportunity state from the simulation loop.
* Move target selection, engagement-path choice, and action selection behind explicit strategy or policy boundaries.
* Keep movement and attack application in focused combat-action code that can be called by simulation, replay, and future manual control.
* Centralize combat-log event recording around applied battle actions so simulation does not hand-build every event.
* Preserve existing observable behavior for initiative ordering, nearest-opponent targeting, movement, melee attacks, counterattack limits, and replay.
* Add behavior tests that prove the refactor preserves simulation output and replayability.

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
