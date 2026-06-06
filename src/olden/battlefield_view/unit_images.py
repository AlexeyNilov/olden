from dataclasses import dataclass
from pathlib import Path

from olden.combat.units import UnitStack

UNIT_IMAGE_ROUTE = "/unit-images"
UNIT_IMAGE_EXTENSION = ".webp"


@dataclass(frozen=True, slots=True)
class UnitImage:
    href: str
    path: Path


def resolve_unit_image(
    unit_stack: UnitStack,
    image_directory: Path,
    route_path: str = UNIT_IMAGE_ROUTE,
) -> UnitImage | None:
    filename = _unit_image_filename(unit_stack)
    if filename is None:
        return None
    image_path = image_directory / filename
    if not image_path.is_file():
        return None
    return UnitImage(href=f"{route_path.rstrip('/')}/{filename}", path=image_path)


def _unit_image_filename(unit_stack: UnitStack) -> str | None:
    unit_id = unit_stack.definition.id
    filename = f"{unit_id}{UNIT_IMAGE_EXTENSION}"
    if Path(filename).name != filename:
        return None
    return filename
