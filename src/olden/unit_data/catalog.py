from dataclasses import dataclass
from typing import Any

import yaml

from olden.combat.units import AttackCategory, DamageRange, UnitCombatStats, UnitDefinition, UnitFootprint


class UnitCatalogError(ValueError):
    pass


class DuplicateUnitIdError(UnitCatalogError):
    pass


class MissingUnitRecordError(UnitCatalogError):
    pass


class UnitCatalogValidationError(UnitCatalogError):
    pass


@dataclass(frozen=True, slots=True)
class UnitDamageRecord:
    minimum: int
    maximum: int


@dataclass(frozen=True, slots=True)
class UnitModifierRangeRecord:
    minimum: int
    maximum: int


@dataclass(frozen=True, slots=True)
class UnitCombatRecord:
    health: int
    attack: int
    defense: int
    damage: UnitDamageRecord
    morale: UnitModifierRangeRecord
    luck: UnitModifierRangeRecord
    initiative: int
    speed: int
    attack_category: str


@dataclass(frozen=True, slots=True)
class UnitSourceRecord:
    name: str
    url: str
    license: str
    retrieved_on: str
    modified: bool


@dataclass(frozen=True, slots=True)
class UnitRecord:
    id: str
    name: str
    faction: str
    tier: int
    combat: UnitCombatRecord
    source: UnitSourceRecord

    def to_unit_definition(self) -> UnitDefinition:
        try:
            attack_category = AttackCategory(self.combat.attack_category)
        except ValueError as exc:
            msg = f"Unsupported attack_category for unit record: {self.id}"
            raise UnitCatalogValidationError(msg) from exc
        return UnitDefinition(
            id=self.id,
            name=self.name,
            speed=self.combat.speed,
            footprint=UnitFootprint.single_hex(),
            combat=UnitCombatStats(
                health=self.combat.health,
                attack=self.combat.attack,
                defense=self.combat.defense,
                damage=DamageRange(minimum=self.combat.damage.minimum, maximum=self.combat.damage.maximum),
                attack_category=attack_category,
            ),
        )


@dataclass(frozen=True, slots=True)
class UnitCatalog:
    schema_version: int
    license: str
    license_url: str
    records: tuple[UnitRecord, ...]

    def __post_init__(self) -> None:
        seen_ids: set[str] = set()
        for record in self.records:
            if record.id in seen_ids:
                msg = f"Duplicate unit ID: {record.id}"
                raise DuplicateUnitIdError(msg)
            seen_ids.add(record.id)

    def get(self, unit_id: str) -> UnitRecord:
        for record in self.records:
            if record.id == unit_id:
                return record
        msg = f"Missing unit record: {unit_id}"
        raise MissingUnitRecordError(msg)


def load_unit_catalog_yaml(content: str) -> UnitCatalog:
    loaded = yaml.safe_load(content)
    data = _require_mapping(loaded, "catalog")
    units = _require_list(data, "units", "catalog")
    _raise_for_duplicate_ids(units)

    return UnitCatalog(
        schema_version=_require_int(data, "schema_version", "catalog", minimum=1),
        license=_require_str(data, "license", "catalog"),
        license_url=_require_str(data, "license_url", "catalog"),
        records=tuple(_parse_unit_record(unit, f"units[{index}]") for index, unit in enumerate(units)),
    )


def _parse_unit_record(value: object, path: str) -> UnitRecord:
    data = _require_mapping(value, path)
    return UnitRecord(
        id=_require_str(data, "id", path),
        name=_require_str(data, "name", path),
        faction=_require_str(data, "faction", path),
        tier=_require_int(data, "tier", path, minimum=1),
        combat=_parse_combat_record(_required(data, "combat", path), f"{path}.combat"),
        source=_parse_source_record(_required(data, "source", path), f"{path}.source"),
    )


def _parse_combat_record(value: object, path: str) -> UnitCombatRecord:
    data = _require_mapping(value, path)
    return UnitCombatRecord(
        health=_require_int(data, "health", path, minimum=1),
        attack=_require_int(data, "attack", path, minimum=0),
        defense=_require_int(data, "defense", path, minimum=0),
        damage=_parse_damage_record(_required(data, "damage", path), f"{path}.damage"),
        morale=_parse_modifier_range_record(_required(data, "morale", path), f"{path}.morale"),
        luck=_parse_modifier_range_record(_required(data, "luck", path), f"{path}.luck"),
        initiative=_require_int(data, "initiative", path, minimum=0),
        speed=_require_int(data, "speed", path, minimum=0),
        attack_category=_require_str(data, "attack_category", path),
    )


def _parse_damage_record(value: object, path: str) -> UnitDamageRecord:
    data = _require_mapping(value, path)
    damage = UnitDamageRecord(
        minimum=_require_int(data, "min", path, minimum=0),
        maximum=_require_int(data, "max", path, minimum=0),
    )
    if damage.maximum < damage.minimum:
        msg = f"{path}.max must be greater than or equal to {path}.min"
        raise UnitCatalogValidationError(msg)
    return damage


def _parse_modifier_range_record(value: object, path: str) -> UnitModifierRangeRecord:
    data = _require_mapping(value, path)
    modifier_range = UnitModifierRangeRecord(
        minimum=_require_int(data, "min", path),
        maximum=_require_int(data, "max", path),
    )
    if modifier_range.maximum < modifier_range.minimum:
        msg = f"{path}.max must be greater than or equal to {path}.min"
        raise UnitCatalogValidationError(msg)
    return modifier_range


def _parse_source_record(value: object, path: str) -> UnitSourceRecord:
    data = _require_mapping(value, path)
    return UnitSourceRecord(
        name=_require_str(data, "name", path),
        url=_require_str(data, "url", path),
        license=_require_str(data, "license", path),
        retrieved_on=_require_str(data, "retrieved_on", path),
        modified=_require_bool(data, "modified", path),
    )


def _raise_for_duplicate_ids(units: list[object]) -> None:
    seen_ids: set[str] = set()
    for index, unit in enumerate(units):
        unit_id = _require_str(_require_mapping(unit, f"units[{index}]"), "id", f"units[{index}]")
        if unit_id in seen_ids:
            msg = f"Duplicate unit ID: {unit_id}"
            raise DuplicateUnitIdError(msg)
        seen_ids.add(unit_id)


def _require_mapping(value: object, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        msg = f"{path} must be a mapping"
        raise UnitCatalogValidationError(msg)
    return value


def _require_list(data: dict[str, Any], key: str, path: str) -> list[object]:
    value = _required(data, key, path)
    if not isinstance(value, list):
        msg = f"{path}.{key} must be a list"
        raise UnitCatalogValidationError(msg)
    return value


def _required(data: dict[str, Any], key: str, path: str) -> object:
    if key not in data:
        msg = f"{path}.{key} is required"
        raise UnitCatalogValidationError(msg)
    return data[key]


def _require_str(data: dict[str, Any], key: str, path: str) -> str:
    value = _required(data, key, path)
    if not isinstance(value, str) or not value:
        msg = f"{path}.{key} must be a non-empty string"
        raise UnitCatalogValidationError(msg)
    return value


def _require_bool(data: dict[str, Any], key: str, path: str) -> bool:
    value = _required(data, key, path)
    if not isinstance(value, bool):
        msg = f"{path}.{key} must be a boolean"
        raise UnitCatalogValidationError(msg)
    return value


def _require_int(data: dict[str, Any], key: str, path: str, minimum: int | None = None) -> int:
    value = _required(data, key, path)
    if not isinstance(value, int) or isinstance(value, bool):
        msg = f"{path}.{key} must be an integer"
        raise UnitCatalogValidationError(msg)
    if minimum is not None and value < minimum:
        msg = f"{path}.{key} must be at least {minimum}"
        raise UnitCatalogValidationError(msg)
    return value
