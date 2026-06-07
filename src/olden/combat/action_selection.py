from enum import Enum


class CombatAction(Enum):
    MELEE_ENGAGE = "melee_engage"
    STAY_OUT_OF_MELEE_REACH = "stay_out_of_melee_reach"
    WAIT = "wait"
    SKIP = "skip"


class CombatActionSelectionError(ValueError):
    pass
