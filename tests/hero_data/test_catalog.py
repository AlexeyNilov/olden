import pytest

from olden.hero_data.catalog import (
    DuplicateHeroIdError,
    HeroCatalogValidationError,
    MissingHeroRecordError,
    load_hero_catalog_yaml,
)
from olden.hero_data.packaged import load_packaged_hero_catalog

VALID_CATALOG_YAML = """
schema_version: 1
license: CC-BY-SA-4.0
license_url: https://creativecommons.org/licenses/by-sa/4.0/
heroes:
  - id: john_johnson
    name: John Johnson
    faction: temple
    hero_class: Knight
    base_stats:
      attack: 2
      defense: 3
      spell_power: 1
      knowledge: 1
    starting_skills:
      - Righteousness
      - Defense
    starting_spell: null
    specialty:
      name: Salt of the Earth
      description: Swordsman-focused specialty.
    source:
      name: "Heroes of Might and Magic: Olden Era Official Wiki"
      url: https://wiki.hoodedhorse.com/Heroes_of_Might_and_Magic_Olden_Era/John_Johnson
      license: CC-BY-SA-4.0
      retrieved_on: "2026-06-13"
      modified: true
"""


def test_hero_catalog_loads_records_by_stable_hero_id():
    catalog = load_hero_catalog_yaml(VALID_CATALOG_YAML)

    record = catalog.get("john_johnson")

    assert record.id == "john_johnson"
    assert record.name == "John Johnson"
    assert record.faction == "temple"
    assert record.hero_class == "Knight"
    assert record.base_stats.attack == 2
    assert record.base_stats.defense == 3
    assert record.base_stats.spell_power == 1
    assert record.base_stats.knowledge == 1
    assert record.starting_skills == ("Righteousness", "Defense")
    assert record.starting_spell is None
    assert record.specialty.name == "Salt of the Earth"
    assert record.source.url == "https://wiki.hoodedhorse.com/Heroes_of_Might_and_Magic_Olden_Era/John_Johnson"


def test_hero_record_converts_to_current_combat_hero():
    hero = load_hero_catalog_yaml(VALID_CATALOG_YAML).get("john_johnson").to_hero()

    assert hero.id == "john_johnson"
    assert hero.name == "John Johnson"
    assert hero.level == 1
    assert hero.experience == 0
    assert hero.stats.attack == 2
    assert hero.stats.defense == 3
    assert hero.stats.spell_power == 1
    assert hero.stats.knowledge == 1


def test_hero_catalog_rejects_duplicate_hero_ids():
    duplicate_catalog = VALID_CATALOG_YAML.replace(
        "  - id: john_johnson",
        "  - id: john_johnson\n    name: Copy\n  - id: john_johnson",
        1,
    )

    with pytest.raises(DuplicateHeroIdError, match="john_johnson"):
        load_hero_catalog_yaml(duplicate_catalog)


def test_hero_catalog_raises_dedicated_error_for_missing_hero_id():
    catalog = load_hero_catalog_yaml(VALID_CATALOG_YAML)

    with pytest.raises(MissingHeroRecordError, match="missing"):
        catalog.get("missing")


def test_hero_catalog_rejects_malformed_required_fields_before_exposing_records():
    malformed_catalog = VALID_CATALOG_YAML.replace("attack: 2", "attack: -1")

    with pytest.raises(HeroCatalogValidationError, match="attack"):
        load_hero_catalog_yaml(malformed_catalog)


def test_packaged_hero_catalog_loads_john_johnson_record():
    catalog = load_packaged_hero_catalog()

    record = catalog.get("john_johnson")

    assert record.name == "John Johnson"
    assert catalog.license == "CC-BY-SA-4.0"
    assert record.faction == "temple"
    assert record.hero_class == "Knight"
    assert record.base_stats.attack == 2
    assert record.base_stats.defense == 3
    assert record.base_stats.spell_power == 1
    assert record.base_stats.knowledge == 1
    assert record.starting_skills == ("Righteousness", "Defense")
    assert record.starting_spell is None
    assert record.specialty.name == "Salt of the Earth"
    assert record.source.license == "CC-BY-SA-4.0"
    assert record.source.retrieved_on == "2026-06-13"
