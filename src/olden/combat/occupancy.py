from olden.combat.coordinates import HexCoord


class Occupancy:
    def __init__(self, blocked_coordinates: frozenset[HexCoord] = frozenset()) -> None:
        self._blocked_coordinates = blocked_coordinates
        self._unit_by_coord: dict[HexCoord, str] = {}

    def place(self, unit_id: str, coord: HexCoord) -> None:
        self._require_placeable(coord)
        self._unit_by_coord[coord] = unit_id

    def unit_at(self, coord: HexCoord) -> str | None:
        return self._unit_by_coord.get(coord)

    def coordinate_for(self, unit_id: str) -> HexCoord | None:
        for coord, occupant_id in self._unit_by_coord.items():
            if occupant_id == unit_id:
                return coord
        return None

    def can_place_coordinate(self, coord: HexCoord, moving_unit_id: str | None = None) -> bool:
        if coord in self._blocked_coordinates:
            return False
        occupant_id = self._unit_by_coord.get(coord)
        return occupant_id is None or occupant_id == moving_unit_id

    def remove(self, unit_id: str) -> None:
        coord = self.coordinate_for(unit_id)
        if coord is not None:
            del self._unit_by_coord[coord]

    def move(self, unit_id: str, destination: HexCoord) -> None:
        current_coordinate = self.coordinate_for(unit_id)
        if current_coordinate is None:
            msg = f"Cannot move unit without an occupied coordinate: {unit_id}"
            raise ValueError(msg)
        self._require_placeable(destination, moving_unit_id=unit_id)
        self.remove(unit_id)
        self._unit_by_coord[destination] = unit_id

    def _require_placeable(self, coord: HexCoord, moving_unit_id: str | None = None) -> None:
        if coord in self._blocked_coordinates:
            msg = f"Cannot place unit on blocked coordinate: {coord}"
            raise ValueError(msg)
        occupant_id = self._unit_by_coord.get(coord)
        if occupant_id is not None and occupant_id != moving_unit_id:
            msg = f"Coordinate is already occupied: {coord}"
            raise ValueError(msg)
