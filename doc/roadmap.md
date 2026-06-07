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

## Milestone 18: Damage calculation and application split

**Status:** Later

* Review `src/olden/combat/attack.py` responsibilities before adding more damage modifiers.
* Separate pure damage calculation from battle-state mutation.
* Introduce an explicit damage context that carries attacker, defender, selected damage, and future modifier inputs.
* Return damage results without requiring a mutable `Battle`.
* Keep wound carryover, creature deaths, stack removal, and occupancy updates in focused damage-application code.
* Preserve current melee damage behavior: selected unit damage, attack/defense modifier, floor rounding, minimum `1` final damage, wound carryover, and defeated-stack removal.
* Leave hero stats, damage tags, luck, range penalties, abilities, and other deferred modifiers out until their requirements are committed.
* Add behavior tests for pure damage calculation and separate damage application.

## Milestone 19: Combat log replay contract and event application

**Status:** Later

* Decide whether combat logs are authoritative battle-event facts or validation fixtures against current combat rules.
* Centralize combat-log event application so replay, replay-frame generation, tests, and future tools do not duplicate movement and attack replay logic.
* Define how combat-log schema versions and combat-rule versions are represented.
* If combat logs are durable artifacts, include enough event payload to apply logged outcomes without recomputing changed future mechanics.
* If combat logs remain rule-validation artifacts, document that older logs may fail when combat rules intentionally change.
* Preserve current replay validation behavior for movement paths, selected damage, final damage, wound damage, defeated stacks, and counterattacks until the contract changes.
* Add behavior tests that cover centralized event application from an initial battle into final battle state and replay frames.

## Milestone 20: Combat side terminology and army order

**Status:** Next

* Consolidate side terminology around attacker and defender as battle roles.
* Rename `CombatSide.PLAYER` and `CombatSide.ENEMY` to `CombatSide.ATTACKER` and `CombatSide.DEFENDER`.
* Reject old serialized `player` and `enemy` side values rather than maintaining compatibility.
* Keep human control, NPC control, and strategy ownership separate from attacker/defender battle roles.
* Update glossary, requirements, battle setup YAML, sample data, tests, combat logs, battlefield view labels, and strategy-discovery naming consistently.
* Add explicit army-slot order metadata separate from deployment coordinates and stack insertion order.
* Use attacker/defender roles and army-slot order as prerequisites for exact initiative and speed tie-breaking.
* Preserve current behavior during the terminology migration: attacker starts on the left and defender starts on the right.

## Future plans

* Later concern: decide whether exact initiative and speed ties should alternate
  between attacker and defender by odd/even round, as observed in Olden Era
  reference notes, instead of using stable configured order.
* Later concern: replace nearest-opponent target selection with explicit combat
  strategy once multi-stack NPC planning is implemented.
* Later concern: model counterattack capacity as unit combat data, with normal
  melee units defaulting to one counterattack per round, Alert I units allowing
  two counterattacks per round, and Alert II units allowing unlimited
  counterattacks per round.
* Later concern: decide how Guardian Griffin's Loyal Protector passive should
  interact with counterattack capacity, adjacency, and target selection.
* NPC combat strategy
