from olden.battlefield_view.unit_images import resolve_unit_image
from olden.combat.sides import CombatSide
from olden.combat.units import AttackCategory, DamageRange, UnitCombatStats, UnitDefinition, UnitStack


def test_resolve_unit_image_returns_route_when_definition_id_webp_exists(tmp_path):
    stack = _stack_for_unit_id("esquire")
    (tmp_path / "esquire.webp").write_bytes(b"image")

    unit_image = resolve_unit_image(stack, tmp_path)

    assert unit_image is not None
    assert unit_image.href == "/unit-images/esquire.webp"


def test_resolve_unit_image_returns_none_when_definition_id_webp_is_missing(tmp_path):
    stack = _stack_for_unit_id("esquire")

    assert resolve_unit_image(stack, tmp_path) is None


def test_resolve_unit_image_returns_none_when_definition_id_is_not_a_plain_file_stem(tmp_path):
    stack = _stack_for_unit_id("../esquire")

    assert resolve_unit_image(stack, tmp_path) is None


def _stack_for_unit_id(unit_id: str) -> UnitStack:
    definition = UnitDefinition(
        id=unit_id,
        name="Swordsman",
        initiative=5,
        speed=4,
        combat=_combat_stats(),
    )
    return UnitStack(id="attacker-stack", definition=definition, side=CombatSide.ATTACKER, count=10)


def _combat_stats() -> UnitCombatStats:
    return UnitCombatStats(
        health=12,
        attack=4,
        defense=4,
        damage=DamageRange(minimum=2, maximum=3),
        attack_category=AttackCategory.MELEE,
    )
