from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from olden.combat.battle import Battle
from olden.combat.battlefield import Battlefield
from olden.combat.coordinates import HexCoord
from olden.combat.obstacles import Obstacle
from olden.combat.occupancy import Occupancy
from olden.combat.sides import CombatSide
from olden.combat.units import UnitStack
from olden.unit_data.catalog import UnitCatalog


class BattleSetupValidationError(ValueError):
    pass


def load_battle_initial_state_file(path: Path, unit_catalog: UnitCatalog) -> Battle:
    return load_battle_initial_state_yaml(path.read_text(encoding="utf-8"), unit_catalog)


def save_battle_initial_state_file(path: Path, battle: Battle) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_battle_initial_state_yaml(battle), encoding="utf-8")


def load_battle_initial_state_yaml(content: str, unit_catalog: UnitCatalog) -> Battle:
    data = _require_mapping(yaml.safe_load(content), "battle initial state")
    _require_schema_version(data)
    obstacles = _parse_obstacles(_optional_mapping(data, "battlefield", "battle initial state"))
    battlefield = Battlefield.default(obstacles=obstacles)
    occupancy = Occupancy(blocked_coordinates=battlefield.blocked_coordinates)
    unit_stacks = _place_unit_stacks(data, unit_catalog, battlefield, occupancy)
    return Battle(battlefield=battlefield, occupancy=occupancy, unit_stacks=unit_stacks)


def dump_battle_initial_state_yaml(battle: Battle) -> str:
    data = {
        "schema_version": 1,
        "battlefield": {"obstacles": [_dump_obstacle(obstacle) for obstacle in battle.battlefield.obstacles]},
        "unit_stacks": [_dump_unit_stack(battle, stack) for stack in battle.unit_stacks.values()],
    }
    return yaml.safe_dump(data, sort_keys=False)


def _place_unit_stacks(
    data: Mapping[str, Any],
    unit_catalog: UnitCatalog,
    battlefield: Battlefield,
    occupancy: Occupancy,
) -> dict[str, UnitStack]:
    unit_stacks: dict[str, UnitStack] = {}
    for index, value in enumerate(_require_list(data, "unit_stacks", "battle initial state")):
        stack, anchor = _parse_unit_stack(value, f"unit_stacks[{index}]", unit_catalog)
        if stack.id in unit_stacks:
            msg = f"Duplicate unit stack ID: {stack.id}"
            raise BattleSetupValidationError(msg)
        battlefield.require_valid(anchor)
        _place_stack(occupancy, stack, anchor)
        unit_stacks[stack.id] = stack
    return unit_stacks


def _place_stack(occupancy: Occupancy, stack: UnitStack, anchor: HexCoord) -> None:
    try:
        occupancy.place_footprint(stack.id, stack.definition.footprint.coordinates_anchored_at(anchor))
    except ValueError as exc:
        raise BattleSetupValidationError(str(exc)) from exc


def _parse_unit_stack(value: object, path: str, unit_catalog: UnitCatalog) -> tuple[UnitStack, HexCoord]:
    data = _require_mapping(value, path)
    unit_id = _require_str(data, "unit_id", path)
    stack = UnitStack(
        id=_require_str(data, "id", path),
        definition=unit_catalog.get(unit_id).to_unit_definition(),
        side=_parse_side(_require_str(data, "side", path), f"{path}.side"),
        count=_require_int(data, "count", path, minimum=1),
    )
    return stack, _parse_coord(_required(data, "anchor", path), f"{path}.anchor")


def _parse_obstacles(battlefield_data: Mapping[str, Any]) -> tuple[Obstacle, ...]:
    obstacles = _optional_list(battlefield_data, "obstacles", "battlefield")
    return tuple(_parse_obstacle(value, f"battlefield.obstacles[{index}]") for index, value in enumerate(obstacles))


def _parse_obstacle(value: object, path: str) -> Obstacle:
    data = _require_mapping(value, path)
    coordinates = _require_list(data, "coordinates", path)
    return Obstacle(
        name=_require_str(data, "name", path),
        coordinates=frozenset(_parse_coord(coord, f"{path}.coordinates[{index}]") for index, coord in enumerate(coordinates)),
    )


def _parse_coord(value: object, path: str) -> HexCoord:
    data = _require_mapping(value, path)
    return HexCoord(column=_require_int(data, "column", path), row=_require_int(data, "row", path))


def _parse_side(value: str, path: str) -> CombatSide:
    try:
        return CombatSide(value)
    except ValueError as exc:
        msg = f"{path} must be a known combat side"
        raise BattleSetupValidationError(msg) from exc


def _dump_obstacle(obstacle: Obstacle) -> dict[str, object]:
    return {
        "name": obstacle.name,
        "coordinates": [_dump_coord(coord) for coord in sorted(obstacle.coordinates)],
    }


def _dump_unit_stack(battle: Battle, stack: UnitStack) -> dict[str, object]:
    return {
        "id": stack.id,
        "unit_id": stack.definition.id,
        "side": stack.side.value,
        "count": stack.count,
        "anchor": _dump_coord(_single_anchor_for(battle, stack.id)),
    }


def _single_anchor_for(battle: Battle, stack_id: str) -> HexCoord:
    coordinates = battle.occupancy.coordinates_for(stack_id)
    if len(coordinates) != 1:
        msg = f"Initial state serialization requires exactly one anchor for unit stack: {stack_id}"
        raise BattleSetupValidationError(msg)
    return next(iter(coordinates))


def _dump_coord(coord: HexCoord) -> dict[str, int]:
    return {"column": coord.column, "row": coord.row}


def _require_schema_version(data: Mapping[str, Any]) -> None:
    schema_version = _require_int(data, "schema_version", "battle initial state", minimum=1)
    if schema_version != 1:
        msg = f"Unsupported battle initial state schema version: {schema_version}"
        raise BattleSetupValidationError(msg)


def _optional_mapping(data: Mapping[str, Any], key: str, path: str) -> Mapping[str, Any]:
    if key not in data:
        return {}
    return _require_mapping(data[key], f"{path}.{key}")


def _optional_list(data: Mapping[str, Any], key: str, path: str) -> list[object]:
    if key not in data:
        return []
    return _require_list(data, key, path)


def _require_mapping(value: object, path: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        msg = f"{path} must be a mapping"
        raise BattleSetupValidationError(msg)
    return value


def _require_list(data: Mapping[str, Any], key: str, path: str) -> list[object]:
    value = _required(data, key, path)
    if not isinstance(value, list):
        msg = f"{path}.{key} must be a list"
        raise BattleSetupValidationError(msg)
    return value


def _required(data: Mapping[str, Any], key: str, path: str) -> object:
    if key not in data:
        msg = f"{path}.{key} is required"
        raise BattleSetupValidationError(msg)
    return data[key]


def _require_str(data: Mapping[str, Any], key: str, path: str) -> str:
    value = _required(data, key, path)
    if not isinstance(value, str) or not value:
        msg = f"{path}.{key} must be a non-empty string"
        raise BattleSetupValidationError(msg)
    return value


def _require_int(data: Mapping[str, Any], key: str, path: str, minimum: int | None = None) -> int:
    value = _required(data, key, path)
    if not isinstance(value, int) or isinstance(value, bool):
        msg = f"{path}.{key} must be an integer"
        raise BattleSetupValidationError(msg)
    if minimum is not None and value < minimum:
        msg = f"{path}.{key} must be at least {minimum}"
        raise BattleSetupValidationError(msg)
    return value
