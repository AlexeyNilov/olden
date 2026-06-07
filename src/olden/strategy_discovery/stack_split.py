import random
from concurrent.futures import Executor, ProcessPoolExecutor
from dataclasses import dataclass
from typing import TypeAlias

from olden.combat.battle import Battle
from olden.combat.combat_simulation import CombatSimulationResult, MovementPath, simulate_combat
from olden.combat.coordinates import HexCoord
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.units import DamageRange, UnitStack

StackSplitGenome: TypeAlias = tuple[int, ...]
StackSplitEvaluationCache: TypeAlias = dict[StackSplitGenome, "StackSplitEvaluation"]


@dataclass(frozen=True, slots=True)
class StackSplitScenario:
    base_battle: Battle
    attacker_pool_stack_id: str
    unit_pool_size: int
    max_slots: int
    deployment_slots: tuple[HexCoord, ...]
    generated_attacker_stack_id_prefix: str
    max_turns: int = 100

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
        if not self.generated_attacker_stack_id_prefix:
            msg = "Generated attacker stack ID prefix must be non-empty"
            raise ValueError(msg)
        self.base_battle.stack(self.attacker_pool_stack_id)
        for slot in self.deployment_slots:
            self.base_battle.battlefield.require_valid(slot)


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
    genome: StackSplitGenome
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


def materialize_stack_split_battle(scenario: StackSplitScenario, genome: StackSplitGenome) -> Battle:
    validate_stack_split(genome, unit_pool_size=scenario.unit_pool_size, max_slots=scenario.max_slots)
    normalized_genome = _normalize_genome(genome, scenario.max_slots)
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
    )


def evaluate_stack_split(scenario: StackSplitScenario, genome: StackSplitGenome) -> StackSplitEvaluation:
    battle = materialize_stack_split_battle(scenario, genome)
    stack_ids = tuple(battle.unit_stacks)
    result = simulate_combat(
        battle,
        stack_ids=stack_ids,
        path_chooser=first_path,
        damage_chooser=average_damage,
        max_turns=scenario.max_turns,
    )
    return StackSplitEvaluation(
        fitness=_fitness_for_result(scenario, result),
        stop_reason=result.stop_reason.value,
    )


def simulate_stack_split(scenario: StackSplitScenario, genome: StackSplitGenome) -> CombatSimulationResult:
    battle = materialize_stack_split_battle(scenario, genome)
    return simulate_combat(
        battle,
        stack_ids=tuple(battle.unit_stacks),
        path_chooser=first_path,
        damage_chooser=average_damage,
        max_turns=scenario.max_turns,
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
        genomes = _initial_population_genomes(scenario, population_size, random_source)
        population = _evaluate_population(scenario, genomes, evaluation_cache, executor)
        best_individual = _best_individual(population)

        for _ in range(generations):
            next_genomes = [best_individual.genome]
            while len(next_genomes) < population_size:
                first_parent = _select_parent(population, random_source, tournament_size)
                second_parent = _select_parent(population, random_source, tournament_size)
                child = _crossover_stack_split(
                    first_parent.genome,
                    second_parent.genome,
                    scenario.unit_pool_size,
                    scenario.max_slots,
                    random_source,
                )
                if random_source.random() < mutation_rate:
                    child = mutate_stack_split(child, random_source)
                next_genomes.append(child)
            population = _evaluate_population(scenario, tuple(next_genomes), evaluation_cache, executor)
            best_individual = max((best_individual, _best_individual(population)), key=_individual_sort_key)
    finally:
        if executor is not None:
            executor.shutdown()

    return StackSplitDiscoveryResult(best_individual=best_individual, population=population)


def mutate_stack_split(genome: StackSplitGenome, random_source: random.Random) -> StackSplitGenome:
    mutable_genome = list(genome)
    donor_indexes = [index for index, count in enumerate(mutable_genome) if count > 0]
    if not donor_indexes:
        return genome
    donor_index = random_source.choice(donor_indexes)
    receiver_index = random_source.randrange(len(mutable_genome))
    if receiver_index == donor_index and len(mutable_genome) > 1:
        receiver_index = (receiver_index + 1) % len(mutable_genome)
    mutable_genome[donor_index] -= 1
    mutable_genome[receiver_index] += 1
    return tuple(mutable_genome)


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
    score = (
        attacker_surviving_units * 1_000_000
        + attacker_surviving_health * 1_000
        + defender_units_killed * 100
        - result.turns_taken
    )
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


def _initial_population_genomes(
    scenario: StackSplitScenario,
    population_size: int,
    random_source: random.Random,
) -> tuple[StackSplitGenome, ...]:
    baseline = (scenario.unit_pool_size,) + (0,) * (scenario.max_slots - 1)
    random_genomes = tuple(
        _random_stack_split(scenario.unit_pool_size, scenario.max_slots, random_source) for _ in range(population_size - 1)
    )
    return (baseline, *random_genomes)


def _evaluate_population(
    scenario: StackSplitScenario,
    genomes: tuple[StackSplitGenome, ...],
    evaluation_cache: StackSplitEvaluationCache,
    executor: Executor | None,
) -> tuple[StackSplitIndividual, ...]:
    missing_genomes = tuple(dict.fromkeys(genome for genome in genomes if genome not in evaluation_cache))
    if executor is None or len(missing_genomes) < 2:
        for genome in missing_genomes:
            evaluation_cache[genome] = evaluate_stack_split(scenario, genome)
    else:
        evaluations = executor.map(_evaluate_stack_split_worker, ((scenario, genome) for genome in missing_genomes))
        evaluation_cache.update(zip(missing_genomes, evaluations, strict=True))

    return tuple(StackSplitIndividual(genome=genome, evaluation=evaluation_cache[genome]) for genome in genomes)


def _evaluate_stack_split_worker(work_item: tuple[StackSplitScenario, StackSplitGenome]) -> StackSplitEvaluation:
    scenario, genome = work_item
    return evaluate_stack_split(scenario, genome)


def _best_individual(population: tuple[StackSplitIndividual, ...]) -> StackSplitIndividual:
    return max(population, key=_individual_sort_key)


def _individual_sort_key(individual: StackSplitIndividual) -> tuple[int, StackSplitGenome]:
    return (individual.evaluation.fitness.score, individual.genome)


def _select_parent(
    population: tuple[StackSplitIndividual, ...],
    random_source: random.Random,
    tournament_size: int,
) -> StackSplitIndividual:
    competitors = tuple(random_source.choice(population) for _ in range(tournament_size))
    return _best_individual(competitors)


def _crossover_stack_split(
    first_parent: StackSplitGenome,
    second_parent: StackSplitGenome,
    unit_pool_size: int,
    max_slots: int,
    random_source: random.Random,
) -> StackSplitGenome:
    first = _normalize_genome(first_parent, max_slots)
    second = _normalize_genome(second_parent, max_slots)
    child = [first[index] if random_source.randrange(2) == 0 else second[index] for index in range(max_slots)]
    _repair_stack_split(child, unit_pool_size, random_source)
    return tuple(child)


def _repair_stack_split(genome: list[int], unit_pool_size: int, random_source: random.Random) -> None:
    while sum(genome) > unit_pool_size:
        donor_indexes = [index for index, count in enumerate(genome) if count > 0]
        genome[random_source.choice(donor_indexes)] -= 1
    while sum(genome) < unit_pool_size:
        genome[random_source.randrange(len(genome))] += 1
