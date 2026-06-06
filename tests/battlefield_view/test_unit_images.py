from olden.battlefield_view.unit_images import resolve_unit_image
from olden.combat.sides import CombatSide
from olden.combat.units import UnitDefinition, UnitFootprint, UnitStack


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
    definition = UnitDefinition(id=unit_id, name="Swordsman", speed=4, footprint=UnitFootprint.single_hex())
    return UnitStack(id="player-stack", definition=definition, side=CombatSide.PLAYER, count=10)
