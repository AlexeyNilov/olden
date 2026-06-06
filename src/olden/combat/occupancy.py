from olden.combat.coordinates import HexCoord


class Occupancy:
    def __init__(self, blocked_coordinates: frozenset[HexCoord] = frozenset()) -> None:
        self._blocked_coordinates = blocked_coordinates
        self._unit_by_coord: dict[HexCoord, str] = {}

    def place(self, unit_id: str, coord: HexCoord) -> None:
        if coord in self._blocked_coordinates:
            msg = f"Cannot place unit on blocked coordinate: {coord}"
            raise ValueError(msg)
        if coord in self._unit_by_coord:
            msg = f"Coordinate is already occupied: {coord}"
            raise ValueError(msg)
        self._unit_by_coord[coord] = unit_id

    def unit_at(self, coord: HexCoord) -> str | None:
        return self._unit_by_coord.get(coord)
