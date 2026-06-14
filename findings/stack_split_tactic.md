
# Stack-split discovery findings

Observed on 2026-06-07 with `data/genetic_battle.yaml` and
`sample/genetic_strategy_discovery.py`.

The scenario pits 15 player Swordsmen against 20 enemy Swordsmen. Stack-split
strategy discovery found `(1, 1, 1, 0, 12, 0, 0)` with:

* player survivors: 0
* enemy units killed: 10
* turns: 18
* fitness: 982

An exhaustive check of all seven-slot splits of 15 units confirmed that 10 enemy
kills is the current deterministic optimum for this scenario. Several equivalent
genomes also reach the same result, including variants with three 1-unit stacks
and one 12-unit stack in different deployment slots. The unsplit baseline
`(15, 0, 0, 0, 0, 0, 0)` kills 7 enemy units.

Why the split works under the current model:

* Strategy discovery uses average damage, so Swordsman damage `2-3` resolves as
  `2`.
* Swordsmen have equal attack and defense, so each attacking creature deals 2
  final damage before health carry-over.
* Each stack acts once per round, so splitting one army creates more player
  turns.
* Defenders can counterattack at most once per round. A 1-unit stack can absorb
  the enemy 20-stack counterattack, letting later player stacks attack the same
  round without taking retaliation.
* Equal initiative and speed preserve configured stack order, so generated
  player stacks can all act before the enemy stack when configured first.

Interpretation:

* The result is internally consistent with committed simulator behavior.
* It also highlights a strong split-stack incentive. That may be desirable if
  the simulator is intended to reproduce HoMM-style retaliation baiting.
* If the outcome feels too strong, likely design levers are turn-order
  tie-breaking, counterattack availability, target selection, and whether
  stack-split discovery should model only formation or also broader tactical
  behavior.
* Do not change requirements from this observation alone. Promote a rule only
  after deciding the intended combat behavior.
