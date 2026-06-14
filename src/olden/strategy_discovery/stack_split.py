import random
from concurrent.futures import Executor, ProcessPoolExecutor
from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from olden.combat.action_selection import ActionChooser, CombatAction, CombatActionContext
from olden.combat.battle import Battle
from olden.combat.combat_simulation import CombatSimulationResult, MovementPath, simulate_combat
from olden.combat.coordinates import HexCoord
from olden.combat.occupancy import Occupancy
from olden.combat.range import distance_between
from olden.combat.sides import CombatSide
from olden.combat.targeting import TargetingPolicy
from olden.combat.units import DamageRange, UnitStack

StackSplitGenome: TypeAlias = tuple[int, ...]
StackSplitEvaluationCache: TypeAlias = dict["StackSplitStrategy", "StackSplitEvaluation"]


class AttackerWaitPolicy(Enum):
    NEVER = "never"
    FIRST_ACTION_IF_SAFE = "first_action_if_safe"


@dataclass(frozen=True, slots=True)
class StackSplitStrategy:
    stack_counts: StackSplitGenome
    wait_policy: AttackerWaitPolicy = AttackerWaitPolicy.NEVER


@dataclass(frozen=True, slots=True)
class StackSplitScenario:
    base_battle: Battle
    attacker_pool_stack_id: str
    unit_pool_size: int
    max_slots: int
    deployment_slots: tuple[HexCoord, ...]
    generated_attacker_stack_id_prefix: str
    max_turns: int = 100
    targeting_policy: TargetingPolicy = TargetingPolicy.THREAT_REMOVED
    attacker_actions: tuple[CombatAction, ...] = (CombatAction.MELEE_ENGAGE,)
    defender_actions: tuple[CombatAction, ...] = (CombatAction.MELEE_ENGAGE,)

    def __post_init__(self) -> None:
        if self.unit_pool_size < 1:
            msg = "Unit pool size must be positive"
            raise ValueError(msg)
        if self.max_slots < 1:
            msg = "Maximum strategy slots must be positive"
            raise ValueError(msg)
        if len(self.deployment_slots) != self.max_slots:
            msg = "Deployment slot count must match maximum strategy slots"
            raise ValueError(msg)
        if self.max_turns < 1:
            msg = "Maximum simulated turns must be positive"
            raise ValueError(msg)
        if not self.attacker_actions:
            msg = "Attacker combat actions must be non-empty"
            raise ValueError(msg)
        if not self.defender_actions:
            msg = "Defender combat actions must be non-empty"
            raise ValueError(msg)
        if not self.generated_attacker_stack_id_prefix:
            msg = "Generated attacker stack ID prefix must be non-empty"
            raise ValueError(msg)
        self.base_battle.stack(self.attacker_pool_stack_id)
        for slot in self.deployment_slots:
            self.base_battle.battlefield.require_valid(slot)
            occupant_id = self.base_battle.occupancy.unit_at(slot)
            if occupant_id is not None and occupant_id != self.attacker_pool_stack_id:
                msg = f"Deployment slot is occupied by base battle stack: {occupant_id}"
                raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class StackSplitFitness:
    score: int
    attacker_surviving_units: int
    attacker_surviving_health: int
    defender_units_killed: int
    turns_taken: int


@dataclass(frozen=True, slots=True)
class StackSplitEvaluation:
    fitness: StackSplitFitness
    stop_reason: str


@dataclass(frozen=True, slots=True)
class StackSplitIndividual:
    strategy: StackSplitStrategy
    evaluation: StackSplitEvaluation


@dataclass(frozen=True, slots=True)
class StackSplitDiscoveryResult:
    best_individual: StackSplitIndividual
    population: tuple[StackSplitIndividual, ...]


def validate_stack_split(genome: StackSplitGenome, unit_pool_size: int, max_slots: int) -> None:
    if not genome:
        msg = "Stack-split genome must contain at least one slot"
        raise ValueError(msg)
    if len(genome) > max_slots:
        msg = "Stack-split genome cannot contain more than the configured maximum slots"
        raise ValueError(msg)
    if any(count < 0 for count in genome):
        msg = "Stack-split genome cannot contain negative stack counts"
        raise ValueError(msg)
    if sum(genome) != unit_pool_size:
        msg = "Stack-split genome must assign exactly the configured unit pool size"
        raise ValueError(msg)


def materialize_stack_split_battle(scenario: StackSplitScenario, strategy: StackSplitStrategy) -> Battle:
    validate_stack_split(strategy.stack_counts, unit_pool_size=scenario.unit_pool_size, max_slots=scenario.max_slots)
    normalized_genome = _normalize_genome(strategy.stack_counts, scenario.max_slots)
    attacker_pool_stack = scenario.base_battle.stack(scenario.attacker_pool_stack_id)
    occupancy = Occupancy(blocked_coordinates=scenario.base_battle.battlefield.blocked_coordinates)
    unit_stacks: dict[str, UnitStack] = {}

    for index, count in enumerate(normalized_genome, start=1):
        if count == 0:
            continue
        stack_id = f"{scenario.generated_attacker_stack_id_prefix}-{index}"
        stack = UnitStack(
            id=stack_id,
            definition=attacker_pool_stack.definition,
            side=attacker_pool_stack.side,
            count=count,
        )
        occupancy.place(stack_id, scenario.deployment_slots[index - 1])
        unit_stacks[stack_id] = stack

    for stack_id, stack in scenario.base_battle.unit_stacks.items():
        if stack_id == scenario.attacker_pool_stack_id:
            continue
        unit_stacks[stack_id] = stack
        coord = scenario.base_battle.occupancy.coordinate_for(stack_id)
        if coord is None:
            msg = f"Base battle stack has no occupied coordinate: {stack_id}"
            raise ValueError(msg)
        occupancy.place(stack_id, coord)

    return Battle(
        battlefield=scenario.base_battle.battlefield,
        occupancy=occupancy,
        unit_stacks=unit_stacks,
        heroes=dict(scenario.base_battle.heroes),
    )


def evaluate_stack_split(scenario: StackSplitScenario, strategy: StackSplitStrategy) -> StackSplitEvaluation:
    battle = materialize_stack_split_battle(scenario, strategy)
    stack_ids = tuple(battle.unit_stacks)
    result = simulate_combat(
        battle,
        stack_ids=stack_ids,
        path_chooser=first_path,
        damage_chooser=average_damage,
        max_turns=scenario.max_turns,
        targeting_policy=scenario.targeting_policy,
        attacker_actions=scenario.attacker_actions,
        defender_actions=scenario.defender_actions,
        action_chooser=_action_chooser_for_strategy(strategy),
    )
    return StackSplitEvaluation(
        fitness=_fitness_for_result(scenario, result),
        stop_reason=result.stop_reason.value,
    )


def simulate_stack_split(scenario: StackSplitScenario, strategy: StackSplitStrategy) -> CombatSimulationResult:
    battle = materialize_stack_split_battle(scenario, strategy)
    return simulate_combat(
        battle,
        stack_ids=tuple(battle.unit_stacks),
        path_chooser=first_path,
        damage_chooser=average_damage,
        max_turns=scenario.max_turns,
        targeting_policy=scenario.targeting_policy,
        attacker_actions=scenario.attacker_actions,
        defender_actions=scenario.defender_actions,
        action_chooser=_action_chooser_for_strategy(strategy),
    )


def discover_stack_split_strategy(
    scenario: StackSplitScenario,
    random_source: random.Random,
    population_size: int = 24,
    generations: int = 20,
    mutation_rate: float = 0.25,
    tournament_size: int = 3,
    worker_count: int = 1,
) -> StackSplitDiscoveryResult:
    if population_size < 2:
        msg = "Population size must be at least 2"
        raise ValueError(msg)
    if generations < 1:
        msg = "Generation count must be positive"
        raise ValueError(msg)
    if mutation_rate < 0 or mutation_rate > 1:
        msg = "Mutation rate must be between 0 and 1"
        raise ValueError(msg)
    if tournament_size < 1:
        msg = "Tournament size must be positive"
        raise ValueError(msg)
    if worker_count < 1:
        msg = "Worker count must be positive"
        raise ValueError(msg)

    executor = ProcessPoolExecutor(max_workers=worker_count) if worker_count > 1 else None
    try:
        evaluation_cache: StackSplitEvaluationCache = {}
        strategies = _initial_population_strategies(scenario, population_size, random_source)
        population = _evaluate_population(scenario, strategies, evaluation_cache, executor)
        best_individual = _best_individual(population)

        for _ in range(generations):
            next_strategies = [best_individual.strategy]
            while len(next_strategies) < population_size:
                first_parent = _select_parent(population, random_source, tournament_size)
                second_parent = _select_parent(population, random_source, tournament_size)
                child = _crossover_stack_split(
                    first_parent.strategy,
                    second_parent.strategy,
                    scenario.unit_pool_size,
                    scenario.max_slots,
                    random_source,
                )
                if random_source.random() < mutation_rate:
                    child = mutate_stack_split(child, random_source)
                next_strategies.append(child)
            population = _evaluate_population(scenario, tuple(next_strategies), evaluation_cache, executor)
            best_individual = max((best_individual, _best_individual(population)), key=_individual_sort_key)
    finally:
        if executor is not None:
            executor.shutdown()

    return StackSplitDiscoveryResult(best_individual=best_individual, population=population)


def mutate_stack_split(
    strategy: StackSplitStrategy,
    random_source: random.Random,
    mutate_wait_policy: bool | None = None,
) -> StackSplitStrategy:
    if mutate_wait_policy is None:
        mutate_wait_policy = random_source.randrange(2) == 0
    if mutate_wait_policy:
        return StackSplitStrategy(
            stack_counts=strategy.stack_counts,
            wait_policy=_mutate_wait_policy(strategy.wait_policy, random_source),
        )

    mutable_genome = list(strategy.stack_counts)
    donor_indexes = [index for index, count in enumerate(mutable_genome) if count > 0]
    if not donor_indexes:
        return strategy
    donor_index = random_source.choice(donor_indexes)
    receiver_index = random_source.randrange(len(mutable_genome))
    if receiver_index == donor_index and len(mutable_genome) > 1:
        receiver_index = (receiver_index + 1) % len(mutable_genome)
    mutable_genome[donor_index] -= 1
    mutable_genome[receiver_index] += 1
    return StackSplitStrategy(stack_counts=tuple(mutable_genome), wait_policy=strategy.wait_policy)


def average_damage(damage: DamageRange) -> int:
    return (damage.minimum + damage.maximum) // 2


def first_path(paths: tuple[MovementPath, ...]) -> MovementPath:
    return paths[0]


def _fitness_for_result(scenario: StackSplitScenario, result: CombatSimulationResult) -> StackSplitFitness:
    attacker_side = scenario.base_battle.stack(scenario.attacker_pool_stack_id).side
    initial_defender_count = _side_unit_count(scenario.base_battle, side_to_exclude=attacker_side)
    attacker_surviving_units = _side_unit_count(result.battle, side=attacker_side)
    attacker_surviving_health = _side_remaining_health(result.battle, attacker_side)
    defender_units_killed = initial_defender_count - _side_unit_count(result.battle, side_to_exclude=attacker_side)
    max_attacker_health = _side_remaining_health(scenario.base_battle, attacker_side)
    score = (
        (defender_units_killed * (scenario.unit_pool_size + 1) + attacker_surviving_units) * (max_attacker_health + 1)
        + attacker_surviving_health
    ) * (scenario.max_turns + 1) + (scenario.max_turns - result.turns_taken)
    return StackSplitFitness(
        score=score,
        attacker_surviving_units=attacker_surviving_units,
        attacker_surviving_health=attacker_surviving_health,
        defender_units_killed=defender_units_killed,
        turns_taken=result.turns_taken,
    )


def _side_unit_count(battle: Battle, side: CombatSide | None = None, side_to_exclude: CombatSide | None = None) -> int:
    return sum(
        stack.count
        for stack in battle.unit_stacks.values()
        if (side is None or stack.side is side) and (side_to_exclude is None or stack.side is not side_to_exclude)
    )


def _side_remaining_health(battle: Battle, side: CombatSide) -> int:
    total_health = 0
    for stack in battle.unit_stacks.values():
        if stack.side is not side:
            continue
        total_health += stack.count * stack.definition.combat.health - stack.wound_damage
    return total_health


def _normalize_genome(genome: StackSplitGenome, max_slots: int) -> StackSplitGenome:
    return genome + (0,) * (max_slots - len(genome))


def _random_stack_split(unit_pool_size: int, max_slots: int, random_source: random.Random) -> StackSplitGenome:
    slots = [0] * max_slots
    for _ in range(unit_pool_size):
        slots[random_source.randrange(max_slots)] += 1
    return tuple(slots)


def _initial_population_strategies(
    scenario: StackSplitScenario,
    population_size: int,
    random_source: random.Random,
) -> tuple[StackSplitStrategy, ...]:
    baseline = StackSplitStrategy(
        stack_counts=(scenario.unit_pool_size,) + (0,) * (scenario.max_slots - 1),
        wait_policy=AttackerWaitPolicy.NEVER,
    )
    random_strategies = tuple(
        StackSplitStrategy(
            stack_counts=_random_stack_split(scenario.unit_pool_size, scenario.max_slots, random_source),
            wait_policy=random_source.choice(tuple(AttackerWaitPolicy)),
        )
        for _ in range(population_size - 1)
    )
    return (baseline, *random_strategies)


def _evaluate_population(
    scenario: StackSplitScenario,
    strategies: tuple[StackSplitStrategy, ...],
    evaluation_cache: StackSplitEvaluationCache,
    executor: Executor | None,
) -> tuple[StackSplitIndividual, ...]:
    missing_strategies = tuple(dict.fromkeys(strategy for strategy in strategies if strategy not in evaluation_cache))
    if executor is None or len(missing_strategies) < 2:
        for strategy in missing_strategies:
            evaluation_cache[strategy] = evaluate_stack_split(scenario, strategy)
    else:
        evaluations = executor.map(_evaluate_stack_split_worker, ((scenario, strategy) for strategy in missing_strategies))
        evaluation_cache.update(zip(missing_strategies, evaluations, strict=True))

    return tuple(StackSplitIndividual(strategy=strategy, evaluation=evaluation_cache[strategy]) for strategy in strategies)


def _evaluate_stack_split_worker(work_item: tuple[StackSplitScenario, StackSplitStrategy]) -> StackSplitEvaluation:
    scenario, strategy = work_item
    return evaluate_stack_split(scenario, strategy)


def _best_individual(population: tuple[StackSplitIndividual, ...]) -> StackSplitIndividual:
    return max(population, key=_individual_sort_key)


def _individual_sort_key(individual: StackSplitIndividual) -> tuple[int, StackSplitGenome, str]:
    strategy = individual.strategy
    return (individual.evaluation.fitness.score, strategy.stack_counts, strategy.wait_policy.value)


def _select_parent(
    population: tuple[StackSplitIndividual, ...],
    random_source: random.Random,
    tournament_size: int,
) -> StackSplitIndividual:
    competitors = tuple(random_source.choice(population) for _ in range(tournament_size))
    return _best_individual(competitors)


def _crossover_stack_split(
    first_parent: StackSplitStrategy,
    second_parent: StackSplitStrategy,
    unit_pool_size: int,
    max_slots: int,
    random_source: random.Random,
) -> StackSplitStrategy:
    first = _normalize_genome(first_parent.stack_counts, max_slots)
    second = _normalize_genome(second_parent.stack_counts, max_slots)
    child = [first[index] if random_source.randrange(2) == 0 else second[index] for index in range(max_slots)]
    _repair_stack_split(child, unit_pool_size, random_source)
    wait_policy = first_parent.wait_policy if random_source.randrange(2) == 0 else second_parent.wait_policy
    return StackSplitStrategy(stack_counts=tuple(child), wait_policy=wait_policy)


def _repair_stack_split(genome: list[int], unit_pool_size: int, random_source: random.Random) -> None:
    while sum(genome) > unit_pool_size:
        donor_indexes = [index for index, count in enumerate(genome) if count > 0]
        genome[random_source.choice(donor_indexes)] -= 1
    while sum(genome) < unit_pool_size:
        genome[random_source.randrange(len(genome))] += 1


def _mutate_wait_policy(policy: AttackerWaitPolicy, random_source: random.Random) -> AttackerWaitPolicy:
    candidates = tuple(candidate for candidate in AttackerWaitPolicy if candidate is not policy)
    return random_source.choice(candidates)


def _action_chooser_for_strategy(strategy: StackSplitStrategy) -> ActionChooser:
    def choose_action(context: CombatActionContext) -> CombatAction:
        if _should_wait_with_attacker(strategy.wait_policy, context):
            return CombatAction.WAIT
        for action in (
            CombatAction.RANGED_ATTACK,
            CombatAction.LONG_REACH_ATTACK,
            CombatAction.MELEE_ENGAGE,
            CombatAction.STAY_OUT_OF_MELEE_REACH,
            CombatAction.SKIP,
            CombatAction.WAIT,
        ):
            if action in context.applicable_actions:
                return action
        msg = "No combat action is available for stack-split strategy"
        raise ValueError(msg)

    return choose_action


def _should_wait_with_attacker(policy: AttackerWaitPolicy, context: CombatActionContext) -> bool:
    if policy is AttackerWaitPolicy.NEVER:
        return False
    if CombatAction.WAIT not in context.applicable_actions:
        return False
    actor = context.battle.stack(context.actor_id)
    if actor.side is not CombatSide.ATTACKER:
        return False
    if context.turn.round_number != 1:
        return False
    if policy is AttackerWaitPolicy.FIRST_ACTION_IF_SAFE:
        return _is_outside_opponent_melee_engagement_reach(context)
    return False


def _is_outside_opponent_melee_engagement_reach(context: CombatActionContext) -> bool:
    actor_coord = context.battle.occupancy.coordinate_for(context.actor_id)
    opponent_coord = context.battle.occupancy.coordinate_for(context.opponent_id)
    if actor_coord is None or opponent_coord is None:
        return False
    opponent_speed = context.battle.stack(context.opponent_id).definition.speed
    return distance_between(context.battle.battlefield, actor_coord, opponent_coord) > opponent_speed + 1
