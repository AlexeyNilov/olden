from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from olden.combat.action_opportunities import CombatRoundState
from olden.combat.battle import Battle
from olden.combat.combat_log import TurnMarker


class CombatAction(Enum):
    RANGED_ATTACK = "ranged_attack"
    MELEE_ENGAGE = "melee_engage"
    STAY_OUT_OF_MELEE_REACH = "stay_out_of_melee_reach"
    WAIT = "wait"
    SKIP = "skip"


class CombatActionSelectionError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CombatActionContext:
    battle: Battle
    round_state: CombatRoundState
    turn: TurnMarker
    actor_id: str
    opponent_id: str
    applicable_actions: tuple[CombatAction, ...]


ActionChooser = Callable[[CombatActionContext], CombatAction]
