# Backlog

## Entry template

```markdown
* [ ] task description
```

## Actual tasks

* [ ] Fix test
__________________________________________________________________ ERROR collecting tests/battlefield_view/test_replay_app.py ___________________________________________________________________
tests/battlefield_view/test_replay_app.py:121: in <module>
    DEFAULT_PLAYER_START = next(iter(load_default_replay_frames()[0].battle.occupancy.coordinates_for("player-esquire")))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   StopIteration

* [ ] Improve agents rules to avoid the following error in every new chat

The environment doesn’t expose python, so I’ll rerun that check with the project’s available Python command.
Ran python3 -c 'from olden.combat.battle import Battle from olden.combat.battlefield'
The package is not on the system Python path directly. I’ll use the project virtualenv so the sanity check runs against the same code the Makefile uses.


* [ ] Why default population_size is 24
