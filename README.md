# olden

Heroes of Might and Magic: Olden Era combat simulator.

## Documentation map

* `doc/development.md` owns developer workflow and project structure.
* `doc/glossary.md` owns shared project vocabulary.
* `doc/requirements.md` owns current testable system behavior.
* `doc/decisions.md` owns architecture and domain decision history.
* `doc/combat_system_reference.md` captures reviewed external combat-system notes for planning.
* `doc/hex_math.md` owns coordinate-system and hex-math reference notes.
* `doc/roadmap.md` owns future sequencing and deferred scope.
* `TODO.md` owns active implementation tasks only.

## Configuration

The server reads local configuration from `.env`. Values already set in the process
environment take precedence over `.env` values.
