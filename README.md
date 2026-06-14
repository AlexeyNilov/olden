# Heroes of Might and Magic: Olden Era combat simulator

Olden is a Python combat-simulation sandbox for exploring Heroes of Might and
Magic: Olden Era battle mechanics. It models battlefield topology, unit stacks,
movement, melee attacks, counterattacks, replayable combat logs, and a local
browser replay view.

The current research focus is deterministic stack-split strategy discovery:
given a fixed battle setup and player unit pool, the simulator searches initial
army formations, scores the resulting combat simulation, and saves the best
battle plus combat log for inspection.

## Documentation map

* `doc/development.md` owns developer workflow, project structure, and current architecture overview.
* `doc/glossary.md` owns shared project vocabulary.
* `doc/requirements.md` owns current testable system behavior.
* `doc/decisions.md` owns decision history for architecture, domain behavior, data flow, public APIs, and dependencies.
* `doc/wiki/` captures external wiki/reference material for planning.
* `doc/hex_math.md` owns coordinate-system and hex-math reference notes.
* `doc/simulation_setup.md` owns the current local simulation and strategy-discovery setup.
* `findings/` owns exploratory findings from local experiments and analysis.
* `doc/roadmap.md` owns future sequencing and deferred scope.
* `doc/ideas.md` owns loose project ideas that are not yet findings, decisions, requirements, or roadmap items.
* `TODO.md` owns active implementation tasks only.

## Local combat replay view

Install the optional view dependency group to launch the local combat-log replay view:

```bash
pip install -e ".[view]"
olden-combat-replay-view
```

For local development, the Makefile can manage browser-view processes:

```bash
make restart-replay-view
make view-status
```

Managed view logs and pid files are written under `.run/`.
