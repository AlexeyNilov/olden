from dataclasses import dataclass
from typing import Any

import yaml

from olden.combat.heroes import Hero, HeroStats


class HeroCatalogError(ValueError):
    pass


class DuplicateHeroIdError(HeroCatalogError):
    pass


class MissingHeroRecordError(HeroCatalogError):
    pass


class HeroCatalogValidationError(HeroCatalogError):
    pass


@dataclass(frozen=True, slots=True)
class HeroBaseStatsRecord:
    attack: int
    defense: int
    spell_power: int
    knowledge: int


@dataclass(frozen=True, slots=True)
class HeroSpecialtyRecord:
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class HeroSourceRecord:
    name: str
    url: str
    license: str
    retrieved_on: str
    modified: bool


@dataclass(frozen=True, slots=True)
class HeroRecord:
    id: str
    name: str
    faction: str
    hero_class: str
    base_stats: HeroBaseStatsRecord
    starting_skills: tuple[str, ...]
    starting_spell: str | None
    specialty: HeroSpecialtyRecord
    source: HeroSourceRecord

    def to_hero(self) -> Hero:
        return Hero(
            id=self.id,
            name=self.name,
            level=1,
            experience=0,
            stats=HeroStats(
                attack=self.base_stats.attack,
                defense=self.base_stats.defense,
                spell_power=self.base_stats.spell_power,
                knowledge=self.base_stats.knowledge,
            ),
        )


@dataclass(frozen=True, slots=True)
class HeroCatalog:
    schema_version: int
    license: str
    license_url: str
    records: tuple[HeroRecord, ...]

    def __post_init__(self) -> None:
        seen_ids: set[str] = set()
        for record in self.records:
            if record.id in seen_ids:
                msg = f"Duplicate hero ID: {record.id}"
                raise DuplicateHeroIdError(msg)
            seen_ids.add(record.id)

    def get(self, hero_id: str) -> HeroRecord:
        for record in self.records:
            if record.id == hero_id:
                return record
        msg = f"Missing hero record: {hero_id}"
        raise MissingHeroRecordError(msg)


def load_hero_catalog_yaml(content: str) -> HeroCatalog:
    loaded = yaml.safe_load(content)
    data = _require_mapping(loaded, "catalog")
    heroes = _require_list(data, "heroes", "catalog")
    _raise_for_duplicate_ids(heroes)

    return HeroCatalog(
        schema_version=_require_int(data, "schema_version", "catalog", minimum=1),
        license=_require_str(data, "license", "catalog"),
        license_url=_require_str(data, "license_url", "catalog"),
        records=tuple(_parse_hero_record(hero, f"heroes[{index}]") for index, hero in enumerate(heroes)),
    )


def _parse_hero_record(value: object, path: str) -> HeroRecord:
    data = _require_mapping(value, path)
    return HeroRecord(
        id=_require_str(data, "id", path),
        name=_require_str(data, "name", path),
        faction=_require_str(data, "faction", path),
        hero_class=_require_str(data, "hero_class", path),
        base_stats=_parse_base_stats_record(_required(data, "base_stats", path), f"{path}.base_stats"),
        starting_skills=_parse_str_tuple(_required(data, "starting_skills", path), f"{path}.starting_skills"),
        starting_spell=_parse_optional_str(data, "starting_spell", path),
        specialty=_parse_specialty_record(_required(data, "specialty", path), f"{path}.specialty"),
        source=_parse_source_record(_required(data, "source", path), f"{path}.source"),
    )


def _parse_base_stats_record(value: object, path: str) -> HeroBaseStatsRecord:
    data = _require_mapping(value, path)
    return HeroBaseStatsRecord(
        attack=_require_int(data, "attack", path, minimum=0),
        defense=_require_int(data, "defense", path, minimum=0),
        spell_power=_require_int(data, "spell_power", path, minimum=0),
        knowledge=_require_int(data, "knowledge", path, minimum=0),
    )


def _parse_specialty_record(value: object, path: str) -> HeroSpecialtyRecord:
    data = _require_mapping(value, path)
    return HeroSpecialtyRecord(
        name=_require_str(data, "name", path),
        description=_require_str(data, "description", path),
    )


def _parse_source_record(value: object, path: str) -> HeroSourceRecord:
    data = _require_mapping(value, path)
    return HeroSourceRecord(
        name=_require_str(data, "name", path),
        url=_require_str(data, "url", path),
        license=_require_str(data, "license", path),
        retrieved_on=_require_str(data, "retrieved_on", path),
        modified=_require_bool(data, "modified", path),
    )


def _parse_str_tuple(value: object, path: str) -> tuple[str, ...]:
    items = _require_list_value(value, path)
    parsed: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, str) or not item:
            msg = f"{path}[{index}] must be a non-empty string"
            raise HeroCatalogValidationError(msg)
        parsed.append(item)
    return tuple(parsed)


def _parse_optional_str(data: dict[str, Any], key: str, path: str) -> str | None:
    value = _required(data, key, path)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        msg = f"{path}.{key} must be a non-empty string or null"
        raise HeroCatalogValidationError(msg)
    return value


def _raise_for_duplicate_ids(heroes: list[object]) -> None:
    seen_ids: set[str] = set()
    for index, hero in enumerate(heroes):
        hero_id = _require_str(_require_mapping(hero, f"heroes[{index}]"), "id", f"heroes[{index}]")
        if hero_id in seen_ids:
            msg = f"Duplicate hero ID: {hero_id}"
            raise DuplicateHeroIdError(msg)
        seen_ids.add(hero_id)


def _require_mapping(value: object, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        msg = f"{path} must be a mapping"
        raise HeroCatalogValidationError(msg)
    return value


def _require_list(data: dict[str, Any], key: str, path: str) -> list[object]:
    return _require_list_value(_required(data, key, path), f"{path}.{key}")


def _require_list_value(value: object, path: str) -> list[object]:
    if not isinstance(value, list):
        msg = f"{path} must be a list"
        raise HeroCatalogValidationError(msg)
    return value


def _required(data: dict[str, Any], key: str, path: str) -> object:
    if key not in data:
        msg = f"{path}.{key} is required"
        raise HeroCatalogValidationError(msg)
    return data[key]


def _require_str(data: dict[str, Any], key: str, path: str) -> str:
    value = _required(data, key, path)
    if not isinstance(value, str) or not value:
        msg = f"{path}.{key} must be a non-empty string"
        raise HeroCatalogValidationError(msg)
    return value


def _require_bool(data: dict[str, Any], key: str, path: str) -> bool:
    value = _required(data, key, path)
    if not isinstance(value, bool):
        msg = f"{path}.{key} must be a boolean"
        raise HeroCatalogValidationError(msg)
    return value


def _require_int(data: dict[str, Any], key: str, path: str, minimum: int | None = None) -> int:
    value = _required(data, key, path)
    if not isinstance(value, int) or isinstance(value, bool):
        msg = f"{path}.{key} must be an integer"
        raise HeroCatalogValidationError(msg)
    if minimum is not None and value < minimum:
        msg = f"{path}.{key} must be at least {minimum}"
        raise HeroCatalogValidationError(msg)
    return value
