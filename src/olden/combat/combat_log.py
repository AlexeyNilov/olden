from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from olden.combat.attack import AttackDamageResult, MeleeAttackResult
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


@dataclass(frozen=True, slots=True)
class UnitWaitedEvent:
    sequence: int
    turn: TurnMarker
    stack_id: str


@dataclass(frozen=True, slots=True)
class UnitSkippedEvent:
    sequence: int
    turn: TurnMarker
    stack_id: str


@dataclass(frozen=True, slots=True)
class AttackDamageEventData:
    selected_damage: int
    final_damage: int
    creatures_killed: int
    defender_count_before: int
    defender_count_after: int
    defender_wound_damage_after: int
    defender_defeated: bool


@dataclass(frozen=True, slots=True)
class UnitAttackedEvent:
    sequence: int
    turn: TurnMarker
    attacker_id: str
    defender_id: str
    primary_damage: AttackDamageEventData
    counterattack: AttackDamageEventData | None


CombatLogEvent = BattleStartedEvent | UnitMovedEvent | UnitWaitedEvent | UnitSkippedEvent | UnitAttackedEvent


@dataclass(slots=True)
class CombatLogReplayState:
    counterattacked_stack_ids_by_round: set[tuple[int, str]] = field(default_factory=set)


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

    def record_unit_waited(self, turn: TurnMarker, stack_id: str) -> UnitWaitedEvent:
        event = UnitWaitedEvent(sequence=self._next_sequence(), turn=turn, stack_id=stack_id)
        self._events.append(event)
        return event

    def record_unit_skipped(self, turn: TurnMarker, stack_id: str) -> UnitSkippedEvent:
        event = UnitSkippedEvent(sequence=self._next_sequence(), turn=turn, stack_id=stack_id)
        self._events.append(event)
        return event

    def record_unit_attacked(self, turn: TurnMarker, attack: MeleeAttackResult) -> UnitAttackedEvent:
        event = UnitAttackedEvent(
            sequence=self._next_sequence(),
            turn=turn,
            attacker_id=attack.primary_damage.attacker_id,
            defender_id=attack.primary_damage.defender_id,
            primary_damage=snapshot_attack_damage(attack.primary_damage),
            counterattack=snapshot_attack_damage(attack.counterattack) if attack.counterattack is not None else None,
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
    replay_state = CombatLogReplayState()
    for event in combat_log.events:
        apply_combat_log_event(battle, event, replay_state)
    return battle


def apply_combat_log_event(battle: Battle, event: CombatLogEvent, replay_state: CombatLogReplayState) -> bool:
    """Apply one event and return whether it changed battle state."""
    if isinstance(event, BattleStartedEvent):
        return False
    if isinstance(event, UnitMovedEvent):
        _apply_unit_moved_event(battle, event)
        return True
    if isinstance(event, UnitWaitedEvent | UnitSkippedEvent):
        return True
    if isinstance(event, UnitAttackedEvent):
        _apply_unit_attacked_event(battle, event, replay_state)
        return True
    return False


def _apply_unit_moved_event(battle: Battle, event: UnitMovedEvent) -> None:
    from olden.combat.combat_actions import apply_logged_movement_action

    apply_logged_movement_action(battle, event)


def _apply_unit_attacked_event(
    battle: Battle,
    event: UnitAttackedEvent,
    replay_state: CombatLogReplayState,
) -> None:
    from olden.combat.combat_actions import apply_logged_melee_attack_action

    apply_logged_melee_attack_action(battle, event, replay_state)


def _parse_event(value: object, index: int) -> CombatLogEvent:
    path = f"events[{index}]"
    data = _require_mapping(value, path)
    event_type = _require_str(data, "type", path)
    if event_type == "battle_started":
        return BattleStartedEvent(sequence=_require_int(data, "sequence", path, minimum=1))
    if event_type == "unit_moved":
        return _parse_unit_moved_event(data, path)
    if event_type == "unit_waited":
        return _parse_unit_waited_event(data, path)
    if event_type == "unit_skipped":
        return _parse_unit_skipped_event(data, path)
    if event_type == "unit_attacked":
        return _parse_unit_attacked_event(data, path)
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


def _parse_unit_waited_event(data: Mapping[str, Any], path: str) -> UnitWaitedEvent:
    return UnitWaitedEvent(
        sequence=_require_int(data, "sequence", path, minimum=1),
        turn=TurnMarker(
            round_number=_require_int(data, "round", path, minimum=1),
            turn_number=_require_int(data, "turn", path, minimum=1),
        ),
        stack_id=_require_str(data, "stack_id", path),
    )


def _parse_unit_skipped_event(data: Mapping[str, Any], path: str) -> UnitSkippedEvent:
    return UnitSkippedEvent(
        sequence=_require_int(data, "sequence", path, minimum=1),
        turn=TurnMarker(
            round_number=_require_int(data, "round", path, minimum=1),
            turn_number=_require_int(data, "turn", path, minimum=1),
        ),
        stack_id=_require_str(data, "stack_id", path),
    )


def _parse_unit_attacked_event(data: Mapping[str, Any], path: str) -> UnitAttackedEvent:
    return UnitAttackedEvent(
        sequence=_require_int(data, "sequence", path, minimum=1),
        turn=TurnMarker(
            round_number=_require_int(data, "round", path, minimum=1),
            turn_number=_require_int(data, "turn", path, minimum=1),
        ),
        attacker_id=_require_str(data, "attacker_id", path),
        defender_id=_require_str(data, "defender_id", path),
        primary_damage=_parse_attack_damage(_required(data, "primary_damage", path), f"{path}.primary_damage"),
        counterattack=_parse_optional_attack_damage(data, "counterattack", path),
    )


def _dump_event(event: CombatLogEvent) -> dict[str, object]:
    if isinstance(event, BattleStartedEvent):
        return {"sequence": event.sequence, "type": "battle_started"}
    if isinstance(event, UnitMovedEvent):
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
    if isinstance(event, UnitWaitedEvent):
        return {
            "sequence": event.sequence,
            "type": "unit_waited",
            "round": event.turn.round_number,
            "turn": event.turn.turn_number,
            "stack_id": event.stack_id,
        }
    if isinstance(event, UnitSkippedEvent):
        return {
            "sequence": event.sequence,
            "type": "unit_skipped",
            "round": event.turn.round_number,
            "turn": event.turn.turn_number,
            "stack_id": event.stack_id,
        }
    data: dict[str, object] = {
        "sequence": event.sequence,
        "type": "unit_attacked",
        "round": event.turn.round_number,
        "turn": event.turn.turn_number,
        "attacker_id": event.attacker_id,
        "defender_id": event.defender_id,
        "primary_damage": _dump_attack_damage(event.primary_damage),
    }
    if event.counterattack is not None:
        data["counterattack"] = _dump_attack_damage(event.counterattack)
    return data


def snapshot_attack_damage(damage: AttackDamageResult) -> AttackDamageEventData:
    return AttackDamageEventData(
        selected_damage=damage.selected_damage,
        final_damage=damage.final_damage,
        creatures_killed=damage.creatures_killed,
        defender_count_before=damage.defender_count_before,
        defender_count_after=damage.defender_count_after,
        defender_wound_damage_after=damage.defender_wound_damage_after,
        defender_defeated=damage.defender_defeated,
    )


def _parse_optional_attack_damage(data: Mapping[str, Any], key: str, path: str) -> AttackDamageEventData | None:
    if key not in data:
        return None
    return _parse_attack_damage(data[key], f"{path}.{key}")


def _parse_attack_damage(value: object, path: str) -> AttackDamageEventData:
    data = _require_mapping(value, path)
    return AttackDamageEventData(
        selected_damage=_require_int(data, "selected_damage", path, minimum=0),
        final_damage=_require_int(data, "final_damage", path, minimum=1),
        creatures_killed=_require_int(data, "creatures_killed", path, minimum=0),
        defender_count_before=_require_int(data, "defender_count_before", path, minimum=1),
        defender_count_after=_require_int(data, "defender_count_after", path, minimum=0),
        defender_wound_damage_after=_require_int(data, "defender_wound_damage_after", path, minimum=0),
        defender_defeated=_require_bool(data, "defender_defeated", path),
    )


def _dump_attack_damage(damage: AttackDamageEventData) -> dict[str, object]:
    return {
        "selected_damage": damage.selected_damage,
        "final_damage": damage.final_damage,
        "creatures_killed": damage.creatures_killed,
        "defender_count_before": damage.defender_count_before,
        "defender_count_after": damage.defender_count_after,
        "defender_wound_damage_after": damage.defender_wound_damage_after,
        "defender_defeated": damage.defender_defeated,
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


def _require_bool(data: Mapping[str, Any], key: str, path: str) -> bool:
    value = _required(data, key, path)
    if not isinstance(value, bool):
        msg = f"{path}.{key} must be a boolean"
        raise CombatLogValidationError(msg)
    return value
