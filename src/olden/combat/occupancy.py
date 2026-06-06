from olden.combat.coordinates import HexCoord


class Occupancy:
    def __init__(self, blocked_coordinates: frozenset[HexCoord] = frozenset()) -> None:
        self._blocked_coordinates = blocked_coordinates
        self._unit_by_coord: dict[HexCoord, str] = {}

    def place(self, unit_id: str, coord: HexCoord) -> None:
        self.place_footprint(unit_id, frozenset({coord}))

    def place_footprint(self, unit_id: str, coordinates: frozenset[HexCoord]) -> None:
        self._require_placeable(coordinates)
        for coord in coordinates:
            self._unit_by_coord[coord] = unit_id

    def unit_at(self, coord: HexCoord) -> str | None:
        return self._unit_by_coord.get(coord)

    def coordinates_for(self, unit_id: str) -> frozenset[HexCoord]:
        return frozenset(coord for coord, occupant_id in self._unit_by_coord.items() if occupant_id == unit_id)

    def can_place(self, coordinates: frozenset[HexCoord], moving_unit_id: str | None = None) -> bool:
        try:
            self._require_placeable(coordinates, moving_unit_id)
        except ValueError:
            return False
        return True

    def remove(self, unit_id: str) -> None:
        for coord in self.coordinates_for(unit_id):
            del self._unit_by_coord[coord]

    def move(self, unit_id: str, destination: HexCoord) -> None:
        current_coordinates = self.coordinates_for(unit_id)
        if len(current_coordinates) != 1:
            msg = f"Single-hex movement requires exactly one occupied coordinate for unit: {unit_id}"
            raise ValueError(msg)
        destination_coordinates = frozenset({destination})
        self._require_placeable(destination_coordinates, moving_unit_id=unit_id)
        self.remove(unit_id)
        self._unit_by_coord[destination] = unit_id

    def _require_placeable(self, coordinates: frozenset[HexCoord], moving_unit_id: str | None = None) -> None:
        for coord in coordinates:
            if coord in self._blocked_coordinates:
                msg = f"Cannot place unit on blocked coordinate: {coord}"
                raise ValueError(msg)
            occupant_id = self._unit_by_coord.get(coord)
            if occupant_id is not None and occupant_id != moving_unit_id:
                msg = f"Coordinate is already occupied: {coord}"
                raise ValueError(msg)
