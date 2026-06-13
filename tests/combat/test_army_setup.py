import pytest

from olden.combat.army_setup import (
    ArmySetupValidationError,
    dump_army_yaml,
    load_army_yaml,
    save_army_file,
)
from olden.combat.sides import CombatSide
from olden.unit_data.catalog import (
    UnitCatalog,
    UnitCombatRecord,
    UnitDamageRecord,
    UnitModifierRangeRecord,
    UnitRecord,
    UnitSourceRecord,
)


def test_load_army_yaml_resolves_units_from_catalog():
    army = load_army_yaml(
        """\
schema_version: 1
side: attacker
unit_stacks:
  - id: attacker-esquire
    unit_id: esquire
    count: 20
  - id: attacker-crossbowman
    unit_id: crossbowman
    count: 12
""",
        _catalog(),
    )

    assert army.side is CombatSide.ATTACKER
    assert [stack.id for stack in army.stacks] == ["attacker-esquire", "attacker-crossbowman"]
    assert [stack.definition.id for stack in army.stacks] == ["esquire", "crossbowman"]
    assert [stack.count for stack in army.stacks] == [20, 12]
    assert all(stack.side is CombatSide.ATTACKER for stack in army.stacks)


def test_dump_army_yaml_round_trips_through_loader(tmp_path):
    catalog = _catalog()
    army = load_army_yaml(
        """\
schema_version: 1
side: defender
unit_stacks:
  - id: defender-griffin
    unit_id: griffin
    count: 5
""",
        catalog,
    )
    path = tmp_path / "army.yaml"

    save_army_file(path, army)
    loaded = load_army_yaml(path.read_text(encoding="utf-8"), catalog)

    assert loaded == army
    assert load_army_yaml(dump_army_yaml(army), catalog) == army


def test_load_army_yaml_rejects_unsupported_schema_version():
    with pytest.raises(ArmySetupValidationError, match="Unsupported army setup schema version"):
        load_army_yaml(
            """\
schema_version: 2
side: attacker
unit_stacks: []
""",
            _catalog(),
        )


def test_load_army_yaml_rejects_duplicate_stack_ids():
    with pytest.raises(ArmySetupValidationError, match="Duplicate unit stack ID"):
        load_army_yaml(
            """\
schema_version: 1
side: attacker
unit_stacks:
  - id: attacker-esquire
    unit_id: esquire
    count: 10
  - id: attacker-esquire
    unit_id: griffin
    count: 5
""",
            _catalog(),
        )


def test_load_army_yaml_rejects_unknown_side():
    with pytest.raises(ArmySetupValidationError, match="side must be a known combat side"):
        load_army_yaml(
            """\
schema_version: 1
side: neutral
unit_stacks: []
""",
            _catalog(),
        )


def test_load_army_yaml_rejects_non_positive_count():
    with pytest.raises(ArmySetupValidationError, match="count must be at least 1"):
        load_army_yaml(
            """\
schema_version: 1
side: attacker
unit_stacks:
  - id: attacker-esquire
    unit_id: esquire
    count: 0
""",
            _catalog(),
        )


def _catalog() -> UnitCatalog:
    return UnitCatalog(
        schema_version=1,
        license="test",
        license_url="https://example.test/license",
        records=(
            _record("esquire", "Swordsman", health=12, damage_min=2, damage_max=3),
            _record("crossbowman", "Crossbowman", health=10, damage_min=2, damage_max=2),
            _record("griffin", "Griffin", health=25, damage_min=5, damage_max=7),
        ),
    )


def _record(unit_id: str, name: str, health: int, damage_min: int, damage_max: int) -> UnitRecord:
    return UnitRecord(
        id=unit_id,
        name=name,
        faction="test",
        tier=1,
        combat=UnitCombatRecord(
            health=health,
            attack=4,
            defense=4,
            damage=UnitDamageRecord(minimum=damage_min, maximum=damage_max),
            morale=UnitModifierRangeRecord(minimum=0, maximum=0),
            luck=UnitModifierRangeRecord(minimum=0, maximum=0),
            initiative=5,
            speed=4,
            attack_category="melee",
        ),
        source=UnitSourceRecord(
            name="test",
            url="https://example.test/unit",
            license="test",
            retrieved_on="2026-06-13",
            modified=False,
        ),
    )
