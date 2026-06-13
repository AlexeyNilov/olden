from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from olden.combat.army import Army
from olden.combat.sides import CombatSide
from olden.combat.units import UnitStack
from olden.unit_data.catalog import UnitCatalog


class ArmySetupValidationError(ValueError):
    pass


def load_army_file(path: Path, unit_catalog: UnitCatalog) -> Army:
    return load_army_yaml(path.read_text(encoding="utf-8"), unit_catalog)


def save_army_file(path: Path, army: Army) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_army_yaml(army), encoding="utf-8")


def load_army_yaml(content: str, unit_catalog: UnitCatalog) -> Army:
    data = _require_mapping(yaml.safe_load(content), "army setup")
    _require_schema_version(data)
    side = _parse_side(_require_str(data, "side", "army setup"), "army setup.side")
    stacks = _parse_unit_stacks(data, unit_catalog, side)
    return Army(side=side, stacks=stacks)


def dump_army_yaml(army: Army) -> str:
    data = {
        "schema_version": 1,
        "side": army.side.value,
        "unit_stacks": [_dump_unit_stack(stack) for stack in army.stacks],
    }
    return yaml.safe_dump(data, sort_keys=False)


def _parse_unit_stacks(data: Mapping[str, Any], unit_catalog: UnitCatalog, side: CombatSide) -> tuple[UnitStack, ...]:
    stacks: list[UnitStack] = []
    seen_ids: set[str] = set()
    for index, value in enumerate(_require_list(data, "unit_stacks", "army setup")):
        stack = _parse_unit_stack(value, f"unit_stacks[{index}]", unit_catalog, side)
        if stack.id in seen_ids:
            msg = f"Duplicate unit stack ID: {stack.id}"
            raise ArmySetupValidationError(msg)
        seen_ids.add(stack.id)
        stacks.append(stack)
    return tuple(stacks)


def _parse_unit_stack(value: object, path: str, unit_catalog: UnitCatalog, side: CombatSide) -> UnitStack:
    data = _require_mapping(value, path)
    unit_id = _require_str(data, "unit_id", path)
    return UnitStack(
        id=_require_str(data, "id", path),
        definition=unit_catalog.get(unit_id).to_unit_definition(),
        side=side,
        count=_require_int(data, "count", path, minimum=1),
    )


def _dump_unit_stack(stack: UnitStack) -> dict[str, object]:
    return {
        "id": stack.id,
        "unit_id": stack.definition.id,
        "count": stack.count,
    }


def _parse_side(value: str, path: str) -> CombatSide:
    try:
        return CombatSide(value)
    except ValueError as exc:
        msg = f"{path} must be a known combat side"
        raise ArmySetupValidationError(msg) from exc


def _require_schema_version(data: Mapping[str, Any]) -> None:
    schema_version = _require_int(data, "schema_version", "army setup", minimum=1)
    if schema_version != 1:
        msg = f"Unsupported army setup schema version: {schema_version}"
        raise ArmySetupValidationError(msg)


def _require_mapping(value: object, path: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        msg = f"{path} must be a mapping"
        raise ArmySetupValidationError(msg)
    return value


def _require_list(data: Mapping[str, Any], key: str, path: str) -> list[object]:
    value = _required(data, key, path)
    if not isinstance(value, list):
        msg = f"{path}.{key} must be a list"
        raise ArmySetupValidationError(msg)
    return value


def _required(data: Mapping[str, Any], key: str, path: str) -> object:
    if key not in data:
        msg = f"{path}.{key} is required"
        raise ArmySetupValidationError(msg)
    return data[key]


def _require_str(data: Mapping[str, Any], key: str, path: str) -> str:
    value = _required(data, key, path)
    if not isinstance(value, str) or not value:
        msg = f"{path}.{key} must be a non-empty string"
        raise ArmySetupValidationError(msg)
    return value


def _require_int(data: Mapping[str, Any], key: str, path: str, minimum: int | None = None) -> int:
    value = _required(data, key, path)
    if not isinstance(value, int) or isinstance(value, bool):
        msg = f"{path}.{key} must be an integer"
        raise ArmySetupValidationError(msg)
    if minimum is not None and value < minimum:
        msg = f"{path}.{key} must be at least {minimum}"
        raise ArmySetupValidationError(msg)
    return value
