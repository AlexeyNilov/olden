from dataclasses import dataclass

DEFAULT_ROW_LENGTHS: tuple[int, ...] = (12, 13, 12, 13, 12, 13, 12, 13, 12, 13, 12)


@dataclass(frozen=True, slots=True, order=True)
class HexCoord:
    column: int
    row: int
