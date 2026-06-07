# Simulation setup

This document describes the current stack-split strategy discovery setup. It is
an explanatory reference for how local simulations are configured and why the
fitness score is shaped the way it is. `doc/requirements.md` remains the
canonical owner for committed testable behavior.

## Current sample

`sample/genetic_strategy_discovery.py` loads the editable
`data/genetic_battle.yaml` initial state and uses the packaged unit catalog. The
sample expects that battle to include the attacker pool stack
`attacker-esquire`; its current unit counts, defender stacks, anchors, and
obstacles come from the YAML file.

The sample searches only for the attacker's initial stack split. It does not
search for turn-level tactics, target choices, spell use, morale handling, luck
handling, or other battle strategy.

The attacker unit pool is assigned to seven fixed deployment slots:

* `HexCoord(0, 9)`
* `HexCoord(0, 8)`
* `HexCoord(0, 7)`
* `HexCoord(0, 6)`
* `HexCoord(0, 5)`
* `HexCoord(0, 4)`
* `HexCoord(0, 3)`

Each genome position maps to one deployment slot. A zero value leaves that slot
empty. A positive value creates one generated attacker stack with that many units.
The genome must assign exactly the full attacker unit pool and cannot contain more
than seven slots or negative counts.

## Evaluation

Each candidate genome is materialized into a battle, then simulated with:

* fixed stack order from the materialized battle
* `first_path`, which picks the first available shortest engagement path
* `average_damage`, which uses `(damage_min + damage_max) // 2`
* `max_turns` of 100 for the stack-split scenario by default

Average damage is intentional for strategy discovery. It removes random damage
variance so a genome has one deterministic score. That makes repeated
evaluations cacheable, makes multiprocessing preserve serial results for the
same seed, and keeps the genetic algorithm from rewarding candidates that only
won a favorable damage roll.

The current combat simulator still applies normal committed combat rules during
evaluation: one action opportunity per living stack per round, nearest living
opponent targeting, movement toward an adjacent engagement hex, attack after
movement if adjacency is reached, and at most one counterattack per defending
stack per round. Deferred mechanics such as morale, luck, waiting, advanced
target selection, and multi-stack battle strategy are not applied.

## Fitness function

The current stack-split fitness score is:

```text
score =
    (((defender_units_killed * (attacker_unit_pool_size + 1)
       + attacker_surviving_units)
       * (maximum_attacker_health + 1)
       + attacker_surviving_health)
       * (max_turns + 1))
       + (max_turns - turns_taken)
```

Where:

* `defender_units_killed` is the initial defender creature count minus the final defender
  creature count.
* `attacker_surviving_units` is the total count of living attacker creatures after
  simulation.
* `attacker_surviving_health` is the total remaining attacker health, including
  current wound damage on surviving stacks.
* `turns_taken` is the number of simulated action opportunities consumed before
  the simulation stops.

The packed score is lexicographic within a scenario:

* Defender units killed dominates all other goals. A strategy that eliminates
  more defenders should beat one that preserves more attackers while making less
  progress toward winning the battle.
* Surviving attacker creatures break ties among strategies with the same defender
  casualties.
* Remaining attacker health breaks ties after survivor count. This favors less
  damaged wins without needing a separate comparison object.
* Faster completion is the final tie-breaker. It is intentionally weak so the
  search does not prefer a quick loss over a slower result with more defender
  casualties.

This fitness function is therefore victory-progress first, then defensive, then
fast. That matches the current use case: discover initial formations that win the
battle by killing all defenders, while still preferring stronger wins among
formations with the same defender casualties.

## Search process

The genetic discovery run starts with an unsplit baseline plus random stack
splits. By default it uses:

* population size: 24
* generations: 20
* max turns: 100
* mutation rate: 0.25
* tournament size: 3
* workers: CPU count minus one, minimum one

`population size` is the number of candidate genomes evaluated in each
generation. A larger population explores more stack splits per generation but
costs more simulations.

`generations` is the number of times the algorithm breeds a new population from
the current one. More generations give selection, crossover, and mutation more
chances to improve the result.

`max turns` is the maximum number of action opportunities simulated for one
candidate battle. It bounds slow or stuck evaluations and can be overridden with
`GENETIC_STRATEGY_DISCOVERY_MAX_TURNS`.

`mutation rate` is the probability that a newly bred child genome is mutated.
The current mutation moves one unit from a non-empty deployment slot to another
slot. A rate of `0.25` means about one in four children gets this extra
variation step. It can be overridden with
`GENETIC_STRATEGY_DISCOVERY_MUTATION_RATE`, which accepts values from `0`
through `1`.

`tournament size` is the number of randomly sampled candidates competing when
choosing each parent. A larger tournament increases selection pressure toward
high-scoring genomes; a smaller tournament preserves more diversity.

Population size, generation count, max turns, mutation rate, and worker count
can be overridden through configuration. Mutation moves one unit from a
non-empty slot to another slot. Crossover chooses each slot from one of two
parents, then repairs the child so the total unit count matches the scenario.

Within a single discovery run, repeated genomes reuse cached deterministic
evaluations. The best individual is selected by score, with the genome tuple as
the deterministic tie-breaker.

## Tuning guidance

Increase `GENETIC_STRATEGY_DISCOVERY_GENERATIONS` first when the discovery run
sometimes finds strong splits but misses them on other runs. More generations
give the algorithm more chances to refine, recombine, and mutate useful
patterns that are already present in the population.

Increase `GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE` when results appear too
dependent on lucky initial candidates. A larger population samples more of the
search space in each generation, but every generation also becomes more
expensive.

For local tuning, prefer increasing generations before increasing population
size. For example, try:

```text
GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE=100
GENETIC_STRATEGY_DISCOVERY_GENERATIONS=150
```

before:

```text
GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE=200
GENETIC_STRATEGY_DISCOVERY_GENERATIONS=50
```

Raise both when reliability matters more than runtime:

```text
GENETIC_STRATEGY_DISCOVERY_POPULATION_SIZE=200
GENETIC_STRATEGY_DISCOVERY_GENERATIONS=150
```

The genetic algorithm is still probabilistic. For small deterministic scenarios,
exhaustive enumeration is a better way to prove the true optimum.

## Outputs

When `sample/genetic_strategy_discovery.py` completes, it writes:

* `data/genetic_best_battle.yaml`
* `data/genetic_best_combat_log.yaml`

These outputs are replay material for inspection. They are not new requirements
by themselves; promote behavior into `doc/requirements.md` only after deciding
that the observed behavior should be committed.
