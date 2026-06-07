import pytest

from olden.combat.units import UnitDefinition
from olden.unit_data.catalog import (
    DuplicateUnitIdError,
    MissingUnitRecordError,
    UnitCatalogValidationError,
    load_unit_catalog_yaml,
)
from olden.unit_data.packaged import load_packaged_unit_catalog

VALID_CATALOG_YAML = """
schema_version: 1
license: CC-BY-SA-4.0
license_url: https://creativecommons.org/licenses/by-sa/4.0/
units:
  - id: esquire
    name: Swordsman
    faction: temple
    tier: 1
    combat:
      health: 12
      attack: 4
      defense: 4
      damage:
        min: 2
        max: 3
      morale:
        min: -5
        max: 5
      luck:
        min: -3
        max: 3
      initiative: 5
      speed: 4
      attack_category: melee
    source:
      name: "Heroes of Might and Magic: Olden Era Official Wiki"
      url: https://wiki.hoodedhorse.com/Heroes_of_Might_and_Magic_Olden_Era/Swordsman
      license: CC-BY-SA-4.0
      retrieved_on: "2026-06-06"
      modified: true
"""


def test_unit_catalog_loads_records_by_stable_unit_id():
    catalog = load_unit_catalog_yaml(VALID_CATALOG_YAML)

    record = catalog.get("esquire")

    assert record.id == "esquire"
    assert record.name == "Swordsman"
    assert record.combat.initiative == 5
    assert record.combat.speed == 4
    assert record.combat.morale.minimum == -5
    assert record.combat.morale.maximum == 5
    assert record.combat.luck.minimum == -3
    assert record.combat.luck.maximum == 3
    assert record.source.url == "https://wiki.hoodedhorse.com/Heroes_of_Might_and_Magic_Olden_Era/Swordsman"


def test_unit_catalog_rejects_duplicate_unit_ids():
    duplicate_catalog = VALID_CATALOG_YAML.replace("  - id: esquire", "  - id: esquire\n    name: Copy\n  - id: esquire", 1)

    with pytest.raises(DuplicateUnitIdError, match="esquire"):
        load_unit_catalog_yaml(duplicate_catalog)


def test_unit_catalog_raises_dedicated_error_for_missing_unit_id():
    catalog = load_unit_catalog_yaml(VALID_CATALOG_YAML)

    with pytest.raises(MissingUnitRecordError, match="archer"):
        catalog.get("archer")


def test_unit_catalog_rejects_malformed_required_fields_before_exposing_records():
    malformed_catalog = VALID_CATALOG_YAML.replace("speed: 4", "speed: -1")
    malformed_initiative_catalog = VALID_CATALOG_YAML.replace("initiative: 5", "initiative: -1")

    with pytest.raises(UnitCatalogValidationError, match="speed"):
        load_unit_catalog_yaml(malformed_catalog)
    with pytest.raises(UnitCatalogValidationError, match="initiative"):
        load_unit_catalog_yaml(malformed_initiative_catalog)


def test_unit_catalog_rejects_inverted_morale_and_luck_ranges():
    inverted_morale_catalog = VALID_CATALOG_YAML.replace("min: -5\n        max: 5", "min: 5\n        max: -5")
    inverted_luck_catalog = VALID_CATALOG_YAML.replace("min: -3\n        max: 3", "min: 3\n        max: -3")

    with pytest.raises(UnitCatalogValidationError, match="morale"):
        load_unit_catalog_yaml(inverted_morale_catalog)
    with pytest.raises(UnitCatalogValidationError, match="luck"):
        load_unit_catalog_yaml(inverted_luck_catalog)


def test_unit_record_converts_to_current_combat_unit_definition():
    catalog = load_unit_catalog_yaml(VALID_CATALOG_YAML)

    definition = catalog.get("esquire").to_unit_definition()

    assert isinstance(definition, UnitDefinition)
    assert definition.id == "esquire"
    assert definition.name == "Swordsman"
    assert definition.initiative == 5
    assert definition.speed == 4
    assert definition.combat.health == 12
    assert definition.combat.attack == 4
    assert definition.combat.defense == 4
    assert definition.combat.damage.minimum == 2
    assert definition.combat.damage.maximum == 3
    assert definition.combat.attack_category.value == "melee"
    assert len(definition.footprint.offsets) == 1


def test_unit_record_rejects_unsupported_attack_category_during_conversion():
    catalog = load_unit_catalog_yaml(VALID_CATALOG_YAML.replace("attack_category: melee", "attack_category: ranged"))

    with pytest.raises(UnitCatalogValidationError, match="attack_category"):
        catalog.get("esquire").to_unit_definition()


def test_packaged_unit_catalog_loads_attributed_sample_records():
    catalog = load_packaged_unit_catalog()

    record = catalog.get("esquire")

    assert record.name == "Swordsman"
    assert catalog.license == "CC-BY-SA-4.0"
    assert record.source.license == "CC-BY-SA-4.0"
    assert record.source.retrieved_on == "2026-06-06"


def test_packaged_unit_catalog_loads_griffin_upgrade_records():
    catalog = load_packaged_unit_catalog()

    temple_griffin = catalog.get("griffin_upg")
    guardian_griffin = catalog.get("griffin_upg_alt")

    assert temple_griffin.name == "Temple Griffin"
    assert temple_griffin.combat.attack == 8
    assert temple_griffin.combat.defense == 6
    assert temple_griffin.combat.damage.minimum == 5
    assert temple_griffin.combat.damage.maximum == 9
    assert temple_griffin.combat.initiative == 12
    assert temple_griffin.combat.speed == 7
    assert temple_griffin.source.url == "https://wiki.hoodedhorse.com/Heroes_of_Might_and_Magic_Olden_Era/Temple_Griffin"

    assert guardian_griffin.name == "Guardian Griffin"
    assert guardian_griffin.combat.attack == 9
    assert guardian_griffin.combat.defense == 10
    assert guardian_griffin.combat.damage.minimum == 7
    assert guardian_griffin.combat.damage.maximum == 7
    assert guardian_griffin.combat.initiative == 10
    assert guardian_griffin.combat.speed == 6
    assert guardian_griffin.source.url == "https://wiki.hoodedhorse.com/Heroes_of_Might_and_Magic_Olden_Era/Guardian_Griffin"
