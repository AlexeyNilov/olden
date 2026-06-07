from olden.combat.battle import Battle
from olden.combat.coordinates import HexCoord
from olden.combat.range import distance_between


def nearest_living_opponent(battle: Battle, actor_id: str, configured_stack_ids: tuple[str, ...]) -> str | None:
    actor = battle.stack(actor_id)
    actor_coord = single_occupied_coordinate(battle, actor_id)
    candidates = tuple(
        stack_id
        for stack_id in configured_stack_ids
        if stack_id in battle.unit_stacks and battle.stack(stack_id).side is not actor.side
    )
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda stack_id: distance_between(
            battle.battlefield,
            actor_coord,
            single_occupied_coordinate(battle, stack_id),
        ),
    )


def one_side_defeated(battle: Battle) -> bool:
    living_sides = {stack.side for stack in battle.unit_stacks.values()}
    return len(living_sides) < 2


def is_defeated(battle: Battle, stack_id: str) -> bool:
    return stack_id not in battle.unit_stacks


def single_occupied_coordinate(battle: Battle, stack_id: str) -> HexCoord:
    coord = battle.occupancy.coordinate_for(stack_id)
    if coord is None:
        msg = f"Expected one occupied coordinate for unit stack: {stack_id}"
        raise ValueError(msg)
    return coord
