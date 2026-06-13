import pytest

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


def test_unit_record_rejects_unsupported_attack_category_during_conversion():
    catalog = load_unit_catalog_yaml(VALID_CATALOG_YAML.replace("attack_category: melee", "attack_category: long_reach"))

    with pytest.raises(UnitCatalogValidationError, match="attack_category"):
        catalog.get("esquire").to_unit_definition()


def test_packaged_unit_catalog_loads_attributed_sample_records():
    catalog = load_packaged_unit_catalog()

    record = catalog.get("esquire")

    assert record.name == "Swordsman"
    assert catalog.license == "CC-BY-SA-4.0"
    assert record.source.license == "CC-BY-SA-4.0"
    assert record.source.retrieved_on == "2026-06-06"


def test_packaged_unit_catalog_loads_crossbowman_record():
    catalog = load_packaged_unit_catalog()

    record = catalog.get("crossbowman")

    assert record.name == "Crossbowman"
    assert record.faction == "temple"
    assert record.tier == 2
    assert record.combat.health == 10
    assert record.combat.attack == 5
    assert record.combat.defense == 3
    assert record.combat.damage.minimum == 3
    assert record.combat.damage.maximum == 4
    assert record.combat.morale.minimum == -5
    assert record.combat.morale.maximum == 5
    assert record.combat.luck.minimum == -3
    assert record.combat.luck.maximum == 3
    assert record.combat.initiative == 5
    assert record.combat.speed == 3
    assert record.combat.attack_category == "ranged"
    assert record.source.url == "https://wiki.hoodedhorse.com/Heroes_of_Might_and_Magic_Olden_Era/Crossbowman"
    assert record.source.retrieved_on == "2026-06-08"


def test_packaged_crossbowman_record_converts_to_ranged_unit_definition():
    catalog = load_packaged_unit_catalog()

    definition = catalog.get("crossbowman").to_unit_definition()

    assert definition.id == "crossbowman"
    assert definition.name == "Crossbowman"
    assert definition.combat.attack_category.value == "ranged"


def test_packaged_unit_catalog_loads_couatl_record():
    catalog = load_packaged_unit_catalog()

    record = catalog.get("coatl")

    assert record.name == "Couatl"
    assert record.faction == "neutral"
    assert record.tier == 6
    assert record.combat.health == 95
    assert record.combat.attack == 26
    assert record.combat.defense == 19
    assert record.combat.damage.minimum == 21
    assert record.combat.damage.maximum == 28
    assert record.combat.morale.minimum == -3
    assert record.combat.morale.maximum == 3
    assert record.combat.luck.minimum == -5
    assert record.combat.luck.maximum == 5
    assert record.combat.initiative == 12
    assert record.combat.speed == 8
    assert record.combat.attack_category == "melee"
    assert record.source.url == "https://wiki.hoodedhorse.com/Heroes_of_Might_and_Magic_Olden_Era/Couatl"
    assert record.source.retrieved_on == "2026-06-13"


def test_packaged_unit_catalog_loads_skeleton_record():
    catalog = load_packaged_unit_catalog()

    record = catalog.get("skeleton")

    assert record.name == "Skeleton"
    assert record.faction == "necropolis"
    assert record.tier == 1
    assert record.combat.health == 6
    assert record.combat.attack == 4
    assert record.combat.defense == 1
    assert record.combat.damage.minimum == 1
    assert record.combat.damage.maximum == 3
    assert record.combat.morale.minimum == 0
    assert record.combat.morale.maximum == 0
    assert record.combat.luck.minimum == -5
    assert record.combat.luck.maximum == 5
    assert record.combat.initiative == 4
    assert record.combat.speed == 3
    assert record.combat.attack_category == "melee"
    assert record.source.url == "https://wiki.hoodedhorse.com/Heroes_of_Might_and_Magic_Olden_Era/Skeleton"
    assert record.source.retrieved_on == "2026-06-13"


@pytest.mark.parametrize(
    (
        "unit_id",
        "name",
        "tier",
        "health",
        "attack",
        "defense",
        "damage_minimum",
        "damage_maximum",
        "initiative",
        "speed",
        "attack_category",
        "wiki_slug",
    ),
    [
        ("skeleton_upg", "Skeleton Warrior", 1, 6, 4, 3, 2, 3, 5, 4, "melee", "Skeleton_Warrior"),
        ("skeleton_upg_alt", "Skeleton Archer", 1, 6, 4, 1, 1, 3, 4, 3, "ranged", "Skeleton_Archer"),
        ("flicker", "Wight", 2, 8, 3, 0, 2, 4, 7, 6, "melee", "Wight"),
        ("flicker_upg", "Wraith", 2, 8, 6, 0, 2, 4, 9, 7, "melee", "Wraith"),
        ("flicker_upg_alt", "Phantasm", 2, 8, 6, 4, 2, 4, 8, 7, "melee", "Phantasm"),
        ("pet", "Undead Pet", 3, 14, 4, 6, 3, 5, 5, 5, "melee", "Undead_Pet"),
        ("pet_upg", "Barghest", 3, 14, 8, 6, 3, 5, 8, 6, "melee", "Barghest"),
        ("pet_upg_alt", "Armored Hound", 3, 18, 4, 8, 3, 5, 5, 5, "melee", "Armored_Hound"),
        ("graverobber", "Graverobber", 4, 30, 11, 9, 6, 8, 4, 3, "long_reach", "Graverobber"),
        ("graverobber_upg", "Merchant of Death", 4, 30, 11, 9, 7, 9, 5, 4, "long_reach", "Merchant_of_Death"),
        ("graverobber_upg_alt", "Kennelmaster", 4, 30, 12, 13, 6, 8, 5, 5, "long_reach", "Kennelmaster"),
        ("lich", "Lich", 5, 45, 12, 12, 12, 16, 4, 2, "ranged", "Lich"),
        ("lich_upg", "Pestilent Lich", 5, 45, 16, 12, 16, 16, 5, 3, "ranged", "Pestilent_Lich"),
        ("lich_upg_alt", "Sanguine Lich", 5, 45, 12, 16, 12, 16, 4, 3, "ranged", "Sanguine_Lich"),
        ("avatar_of_war", "Dread Knight", 6, 100, 19, 18, 12, 14, 9, 7, "melee", "Dread_Knight"),
        ("avatar_of_war_upg", "Avatar of War", 6, 100, 19, 20, 18, 20, 11, 8, "melee", "Avatar_of_War"),
        ("avatar_of_war_upg_alt", "Hollow Reaper", 6, 100, 25, 18, 22, 24, 10, 7, "melee", "Hollow_Reaper"),
        ("vampire", "Vampire", 7, 150, 22, 20, 25, 25, 11, 6, "melee", "Vampire"),
        ("vampire_upg", "Vampire Lord", 7, 175, 22, 27, 30, 30, 13, 8, "melee", "Vampire_Lord"),
        ("vampire_upg_alt", "Vampire Scholar", 7, 150, 25, 20, 30, 30, 12, 5, "long_reach", "Vampire_Scholar"),
    ],
)
def test_packaged_unit_catalog_loads_necropolis_unit_records(
    unit_id,
    name,
    tier,
    health,
    attack,
    defense,
    damage_minimum,
    damage_maximum,
    initiative,
    speed,
    attack_category,
    wiki_slug,
):
    catalog = load_packaged_unit_catalog()

    record = catalog.get(unit_id)

    assert record.name == name
    assert record.faction == "necropolis"
    assert record.tier == tier
    assert record.combat.health == health
    assert record.combat.attack == attack
    assert record.combat.defense == defense
    assert record.combat.damage.minimum == damage_minimum
    assert record.combat.damage.maximum == damage_maximum
    assert record.combat.morale.minimum == 0
    assert record.combat.morale.maximum == 0
    assert record.combat.luck.minimum == -5
    assert record.combat.luck.maximum == 5
    assert record.combat.initiative == initiative
    assert record.combat.speed == speed
    assert record.combat.attack_category == attack_category
    assert record.source.url == f"https://wiki.hoodedhorse.com/Heroes_of_Might_and_Magic_Olden_Era/{wiki_slug}"
    assert record.source.retrieved_on == "2026-06-13"


def test_packaged_unit_catalog_loads_cavalry_record():
    catalog = load_packaged_unit_catalog()

    record = catalog.get("sunlight_cavalry")

    assert record.name == "Cavalry"
    assert record.faction == "temple"
    assert record.tier == 5
    assert record.combat.health == 85
    assert record.combat.attack == 12
    assert record.combat.defense == 17
    assert record.combat.damage.minimum == 10
    assert record.combat.damage.maximum == 14
    assert record.combat.morale.minimum == -5
    assert record.combat.morale.maximum == 5
    assert record.combat.luck.minimum == -3
    assert record.combat.luck.maximum == 3
    assert record.combat.initiative == 10
    assert record.combat.speed == 7
    assert record.combat.attack_category == "melee"
    assert record.source.url == "https://wiki.hoodedhorse.com/Heroes_of_Might_and_Magic_Olden_Era/Cavalry"
    assert record.source.retrieved_on == "2026-06-13"


def test_packaged_unit_catalog_loads_inquisitor_record():
    catalog = load_packaged_unit_catalog()

    record = catalog.get("inquisitor")

    assert record.name == "Inquisitor"
    assert record.faction == "temple"
    assert record.tier == 6
    assert record.combat.health == 95
    assert record.combat.attack == 20
    assert record.combat.defense == 24
    assert record.combat.damage.minimum == 19
    assert record.combat.damage.maximum == 23
    assert record.combat.morale.minimum == -5
    assert record.combat.morale.maximum == 5
    assert record.combat.luck.minimum == -3
    assert record.combat.luck.maximum == 3
    assert record.combat.initiative == 7
    assert record.combat.speed == 4
    assert record.combat.attack_category == "melee"
    assert record.source.url == "https://wiki.hoodedhorse.com/Heroes_of_Might_and_Magic_Olden_Era/Inquisitor"
    assert record.source.retrieved_on == "2026-06-13"


def test_packaged_unit_catalog_loads_angel_record():
    catalog = load_packaged_unit_catalog()

    record = catalog.get("angel")

    assert record.name == "Angel"
    assert record.faction == "temple"
    assert record.tier == 7
    assert record.combat.health == 225
    assert record.combat.attack == 30
    assert record.combat.defense == 30
    assert record.combat.damage.minimum == 50
    assert record.combat.damage.maximum == 75
    assert record.combat.morale.minimum == -3
    assert record.combat.morale.maximum == 3
    assert record.combat.luck.minimum == -3
    assert record.combat.luck.maximum == 3
    assert record.combat.initiative == 8
    assert record.combat.speed == 4
    assert record.combat.attack_category == "ranged"
    assert record.source.url == "https://wiki.hoodedhorse.com/Heroes_of_Might_and_Magic_Olden_Era/Angel"
    assert record.source.retrieved_on == "2026-06-13"
