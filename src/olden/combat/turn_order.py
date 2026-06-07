from olden.combat.battle import Battle


def order_stacks_for_round(battle: Battle, stack_ids: tuple[str, ...]) -> tuple[str, ...]:
    configured_order = {stack_id: index for index, stack_id in enumerate(stack_ids)}
    living_stack_ids = tuple(stack_id for stack_id in stack_ids if stack_id in battle.unit_stacks)
    return tuple(
        sorted(
            living_stack_ids,
            key=lambda stack_id: (
                -battle.stack(stack_id).definition.initiative,
                -battle.stack(stack_id).definition.speed,
                configured_order[stack_id],
            ),
        )
    )
