from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from olden.combat.battle import Battle, MovementResult
from olden.combat.coordinates import HexCoord


class CombatLogValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TurnMarker:
    round_number: int
    turn_number: int

    def __post_init__(self) -> None:
        if self.round_number < 1:
            msg = "Round number must be positive"
            raise ValueError(msg)
        if self.turn_number < 1:
            msg = "Turn number must be positive"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class BattleStartedEvent:
    sequence: int


@dataclass(frozen=True, slots=True)
class UnitMovedEvent:
    sequence: int
    turn: TurnMarker
    stack_id: str
    start: HexCoord
    destination: HexCoord
    path: tuple[HexCoord, ...]


CombatLogEvent = BattleStartedEvent | UnitMovedEvent


class CombatLog:
    def __init__(self, events: tuple[CombatLogEvent, ...] = ()) -> None:
        self._events = list(events)

    @property
    def events(self) -> tuple[CombatLogEvent, ...]:
        return tuple(self._events)

    def record_battle_started(self) -> BattleStartedEvent:
        event = BattleStartedEvent(sequence=self._next_sequence())
        self._events.append(event)
        return event

    def record_unit_moved(self, turn: TurnMarker, movement: MovementResult) -> UnitMovedEvent:
        event = UnitMovedEvent(
            sequence=self._next_sequence(),
            turn=turn,
            stack_id=movement.stack_id,
            start=movement.start,
            destination=movement.destination,
            path=movement.path,
        )
        self._events.append(event)
        return event

    def _next_sequence(self) -> int:
        return len(self._events) + 1


def load_combat_log_file(path: Path) -> CombatLog:
    return load_combat_log_yaml(path.read_text(encoding="utf-8"))


def save_combat_log_file(path: Path, combat_log: CombatLog) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_combat_log_yaml(combat_log), encoding="utf-8")


def load_combat_log_yaml(content: str) -> CombatLog:
    data = _require_mapping(yaml.safe_load(content), "combat log")
    _require_schema_version(data)
    events = tuple(_parse_event(value, index) for index, value in enumerate(_require_list(data, "events", "combat log")))
    _require_contiguous_sequences(events)
    return CombatLog(events)


def dump_combat_log_yaml(combat_log: CombatLog) -> str:
    data = {
        "schema_version": 1,
        "events": [_dump_event(event) for event in combat_log.events],
    }
    return yaml.safe_dump(data, sort_keys=False)


def replay_combat_log(initial_battle: Battle, combat_log: CombatLog) -> Battle:
    battle = initial_battle.copy()
    for event in combat_log.events:
        if isinstance(event, BattleStartedEvent):
            continue
        _replay_unit_moved(battle, event)
    return battle


def _replay_unit_moved(battle: Battle, event: UnitMovedEvent) -> None:
    movement = battle.move_stack(event.stack_id, event.destination)
    if movement.start != event.start or movement.path != event.path:
        msg = f"Combat log movement does not match replayed movement for unit stack: {event.stack_id}"
        raise CombatLogValidationError(msg)


def _parse_event(value: object, index: int) -> CombatLogEvent:
    path = f"events[{index}]"
    data = _require_mapping(value, path)
    event_type = _require_str(data, "type", path)
    if event_type == "battle_started":
        return BattleStartedEvent(sequence=_require_int(data, "sequence", path, minimum=1))
    if event_type == "unit_moved":
        return _parse_unit_moved_event(data, path)
    msg = f"{path}.type is unsupported: {event_type}"
    raise CombatLogValidationError(msg)


def _parse_unit_moved_event(data: Mapping[str, Any], path: str) -> UnitMovedEvent:
    return UnitMovedEvent(
        sequence=_require_int(data, "sequence", path, minimum=1),
        turn=TurnMarker(
            round_number=_require_int(data, "round", path, minimum=1),
            turn_number=_require_int(data, "turn", path, minimum=1),
        ),
        stack_id=_require_str(data, "stack_id", path),
        start=_parse_coord(_required(data, "start", path), f"{path}.start"),
        destination=_parse_coord(_required(data, "destination", path), f"{path}.destination"),
        path=tuple(
            _parse_coord(coord, f"{path}.path[{index}]") for index, coord in enumerate(_require_list(data, "path", path))
        ),
    )


def _dump_event(event: CombatLogEvent) -> dict[str, object]:
    if isinstance(event, BattleStartedEvent):
        return {"sequence": event.sequence, "type": "battle_started"}
    return {
        "sequence": event.sequence,
        "type": "unit_moved",
        "round": event.turn.round_number,
        "turn": event.turn.turn_number,
        "stack_id": event.stack_id,
        "start": _dump_coord(event.start),
        "destination": _dump_coord(event.destination),
        "path": [_dump_coord(coord) for coord in event.path],
    }


def _parse_coord(value: object, path: str) -> HexCoord:
    data = _require_mapping(value, path)
    return HexCoord(column=_require_int(data, "column", path), row=_require_int(data, "row", path))


def _dump_coord(coord: HexCoord) -> dict[str, int]:
    return {"column": coord.column, "row": coord.row}


def _require_schema_version(data: Mapping[str, Any]) -> None:
    schema_version = _require_int(data, "schema_version", "combat log", minimum=1)
    if schema_version != 1:
        msg = f"Unsupported combat log schema version: {schema_version}"
        raise CombatLogValidationError(msg)


def _require_contiguous_sequences(events: tuple[CombatLogEvent, ...]) -> None:
    for expected, event in enumerate(events, start=1):
        if event.sequence != expected:
            msg = f"Combat log event sequence must be contiguous at event {expected}"
            raise CombatLogValidationError(msg)


def _require_mapping(value: object, path: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        msg = f"{path} must be a mapping"
        raise CombatLogValidationError(msg)
    return value


def _require_list(data: Mapping[str, Any], key: str, path: str) -> list[object]:
    value = _required(data, key, path)
    if not isinstance(value, list):
        msg = f"{path}.{key} must be a list"
        raise CombatLogValidationError(msg)
    return value


def _required(data: Mapping[str, Any], key: str, path: str) -> object:
    if key not in data:
        msg = f"{path}.{key} is required"
        raise CombatLogValidationError(msg)
    return data[key]


def _require_str(data: Mapping[str, Any], key: str, path: str) -> str:
    value = _required(data, key, path)
    if not isinstance(value, str) or not value:
        msg = f"{path}.{key} must be a non-empty string"
        raise CombatLogValidationError(msg)
    return value


def _require_int(data: Mapping[str, Any], key: str, path: str, minimum: int | None = None) -> int:
    value = _required(data, key, path)
    if not isinstance(value, int) or isinstance(value, bool):
        msg = f"{path}.{key} must be an integer"
        raise CombatLogValidationError(msg)
    if minimum is not None and value < minimum:
        msg = f"{path}.{key} must be at least {minimum}"
        raise CombatLogValidationError(msg)
    return value
