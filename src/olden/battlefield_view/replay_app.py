from collections.abc import Sequence
from html import escape
from importlib import import_module
from importlib.resources import files
from pathlib import Path
from typing import Any

from olden.battlefield_view.model import build_battlefield_view_for_battle
from olden.battlefield_view.svg import (
    DEFAULT_UNIT_IMAGE_DIRECTORY,
    register_unit_image_static_files,
    render_battlefield_svg,
)
from olden.combat.battle_setup import load_battle_initial_state_file
from olden.combat.combat_log import (
    AttackDamageEventData,
    UnitAttackedEvent,
    UnitMovedEvent,
    UnitSkippedEvent,
    UnitWaitedEvent,
    load_combat_log_file,
)
from olden.combat.combat_replay import CombatReplayFrame, build_combat_replay_frames
from olden.config import DEMO_BATTLE_INITIAL_STATE_PATH, DEMO_COMBAT_LOG_PATH, load_config
from olden.unit_data.packaged import load_packaged_unit_catalog

DEFAULT_REPLAY_DELAY_SECONDS = 1.0
DEFAULT_REPLAY_PORT = 8081
REPLAY_PAGE_CSS_FILENAME = "replay_app.css"


class ReplayController:
    def __init__(
        self,
        frames: Sequence[CombatReplayFrame],
        svg_container: Any,
        log_container: Any,
        status_label: Any,
        timer: Any,
        delay_seconds: float,
        unit_image_directory: Path = DEFAULT_UNIT_IMAGE_DIRECTORY,
    ) -> None:
        if not frames:
            msg = "Combat replay requires at least one frame"
            raise ValueError(msg)
        self.frames = tuple(frames)
        self.svg_container = svg_container
        self.log_container = log_container
        self.status_label = status_label
        self.timer = timer
        self.unit_image_directory = unit_image_directory
        self.current_index = 0
        self.set_delay(delay_seconds)
        self.render_current_frame()

    def start(self) -> None:
        self.timer.activate()

    def pause(self) -> None:
        self.timer.deactivate()

    def restart(self) -> None:
        self.current_index = 0
        self.render_current_frame()

    def previous(self) -> None:
        self.current_index = max(0, self.current_index - 1)
        self.render_current_frame()

    def next(self) -> None:
        self.advance()

    def advance(self) -> None:
        if self.current_index >= len(self.frames) - 1:
            self.pause()
            return
        self.current_index += 1
        self.render_current_frame()
        if self.current_index >= len(self.frames) - 1:
            self.pause()

    def set_delay(self, delay_seconds: float) -> None:
        if delay_seconds <= 0:
            msg = "Replay delay must be positive"
            raise ValueError(msg)
        self.timer.interval = delay_seconds

    def render_current_frame(self) -> None:
        frame = self.frames[self.current_index]
        view = build_battlefield_view_for_battle(frame.battle)
        self.svg_container.set_content(render_battlefield_svg(view, unit_image_directory=self.unit_image_directory))
        self.log_container.set_content(_combat_log_html(self.frames, self.current_index))
        self.status_label.set_text(_frame_status(frame))


def main() -> None:
    config = load_config()
    run_combat_replay_view(
        initial_state_path=config.replay_battle_initial_state_path,
        combat_log_path=config.replay_combat_log_path,
    )


def run_combat_replay_view(
    initial_state_path: Path | None = None,
    combat_log_path: Path | None = None,
    delay_seconds: float = DEFAULT_REPLAY_DELAY_SECONDS,
    port: int = DEFAULT_REPLAY_PORT,
) -> None:
    if initial_state_path is None or combat_log_path is None:
        config = load_config()
        initial_state_path = initial_state_path or config.replay_battle_initial_state_path
        combat_log_path = combat_log_path or config.replay_combat_log_path
    nicegui = _load_nicegui()
    ui = getattr(nicegui, "ui")
    frames = load_replay_frames(initial_state_path, combat_log_path)
    register_unit_image_static_files(getattr(nicegui, "app"), DEFAULT_UNIT_IMAGE_DIRECTORY)
    _build_page(ui, frames, delay_seconds, DEFAULT_UNIT_IMAGE_DIRECTORY)
    ui.run(title="Olden Combat Replay", reload=False, show=False, port=port)


def load_demo_replay_frames() -> tuple[CombatReplayFrame, ...]:
    return load_replay_frames(DEMO_BATTLE_INITIAL_STATE_PATH, DEMO_COMBAT_LOG_PATH)


def load_replay_frames(initial_state_path: Path, combat_log_path: Path) -> tuple[CombatReplayFrame, ...]:
    battle = load_battle_initial_state_file(initial_state_path, load_packaged_unit_catalog())
    combat_log = load_combat_log_file(combat_log_path)
    return build_combat_replay_frames(battle, combat_log)


def load_replay_page_css() -> str:
    return files("olden.battlefield_view").joinpath(REPLAY_PAGE_CSS_FILENAME).read_text(encoding="utf-8")


def _build_page(
    ui: Any,
    frames: Sequence[CombatReplayFrame],
    delay_seconds: float = DEFAULT_REPLAY_DELAY_SECONDS,
    unit_image_directory: Path = DEFAULT_UNIT_IMAGE_DIRECTORY,
) -> ReplayController:
    ui.page_title("Olden Combat Replay")
    ui.add_css(load_replay_page_css())
    with ui.column().classes("w-full items-center q-pa-md"):
        status_label = ui.label("")
        with ui.row().classes("replay-surface"):
            svg_container = ui.html("", sanitize=False).classes("battlefield-view")
            log_container = ui.html("", sanitize=False).classes("combat-log-panel")
        timer_callback = _ReplayTimerCallback()
        timer = ui.timer(delay_seconds, timer_callback, active=False)
        controller = ReplayController(
            frames=frames,
            svg_container=svg_container,
            log_container=log_container,
            status_label=status_label,
            timer=timer,
            delay_seconds=delay_seconds,
            unit_image_directory=unit_image_directory,
        )
        timer_callback.controller = controller
        with ui.row().classes("items-center"):
            ui.button("Play", on_click=controller.start)
            ui.button("Pause", on_click=controller.pause)
            ui.button("Restart", on_click=controller.restart)
            ui.button("Previous", on_click=controller.previous)
            ui.button("Next", on_click=controller.next)
            ui.number(
                "Delay seconds",
                value=delay_seconds,
                min=0.1,
                max=10.0,
                step=0.1,
                on_change=lambda event: controller.set_delay(float(event.value)),
            ).props("dense outlined").classes("replay-delay-input")
    return controller


class _ReplayTimerCallback:
    def __init__(self) -> None:
        self.controller: ReplayController | None = None

    def __call__(self) -> None:
        if self.controller is not None:
            self.controller.advance()


def _frame_status(frame: CombatReplayFrame) -> str:
    prefix = f"Frame {frame.index + 1} / {frame.total}"
    if frame.event is None:
        return f"{prefix} - initial state"
    if isinstance(frame.event, UnitMovedEvent):
        return (
            f"{prefix} - round {frame.event.turn.round_number}, turn {frame.event.turn.turn_number}: "
            f"{escape(frame.event.stack_id)} moved from "
            f"({frame.event.start.column}, {frame.event.start.row}) to "
            f"({frame.event.destination.column}, {frame.event.destination.row})"
        )
    if isinstance(frame.event, UnitAttackedEvent):
        return f"{prefix} - {_attack_text(frame.event)}{_counterattack_status(frame.event.counterattack)}"
    if isinstance(frame.event, UnitWaitedEvent):
        return f"{prefix} - {_wait_text(frame.event)}"
    if isinstance(frame.event, UnitSkippedEvent):
        return f"{prefix} - {_skip_text(frame.event)}"
    return f"{prefix} - event {frame.event.sequence}"


def _combat_log_html(frames: Sequence[CombatReplayFrame], current_index: int) -> str:
    parts = ['<ol class="combat-log">']
    for index, frame in enumerate(frames):
        active_class = " active" if index == current_index else ""
        parts.append(f'<li class="combat-log-entry{active_class}">{_log_entry_html(frame)}</li>')
    parts.append("</ol>")
    return "".join(parts)


def _log_entry_html(frame: CombatReplayFrame) -> str:
    if frame.event is None:
        return '<span class="event-kind">Initial</span><span class="event-detail">Initial battle state</span>'
    if isinstance(frame.event, UnitMovedEvent):
        return f'<span class="event-kind">Move</span><span class="event-detail">{_movement_text(frame.event)}</span>'
    if isinstance(frame.event, UnitAttackedEvent):
        return (
            '<span class="event-kind">Attack</span>'
            f'<span class="event-detail">{_attack_text(frame.event)}</span>'
            f"{_counterattack_html(frame.event.counterattack)}"
        )
    if isinstance(frame.event, UnitWaitedEvent):
        return f'<span class="event-kind">Wait</span><span class="event-detail">{_wait_text(frame.event)}</span>'
    if isinstance(frame.event, UnitSkippedEvent):
        return f'<span class="event-kind">Skip</span><span class="event-detail">{_skip_text(frame.event)}</span>'
    return f'<span class="event-kind">Event</span><span class="event-detail">Event {frame.event.sequence}</span>'


def _movement_text(event: UnitMovedEvent) -> str:
    return (
        f"R{event.turn.round_number} T{event.turn.turn_number}: {escape(event.stack_id)} moved "
        f"({event.start.column}, {event.start.row}) -> "
        f"({event.destination.column}, {event.destination.row})"
    )


def _attack_text(event: UnitAttackedEvent) -> str:
    return (
        f"round {event.turn.round_number}, turn {event.turn.turn_number}: "
        f"{escape(event.attacker_id)} attacked {escape(event.defender_id)}: "
        f"{event.primary_damage.final_damage} damage, "
        f"{event.primary_damage.creatures_killed} killed, "
        f"{escape(event.defender_id)} {event.primary_damage.defender_count_after} left"
    )


def _wait_text(event: UnitWaitedEvent) -> str:
    return f"round {event.turn.round_number}, turn {event.turn.turn_number}: {escape(event.stack_id)} waited"


def _skip_text(event: UnitSkippedEvent) -> str:
    return f"round {event.turn.round_number}, turn {event.turn.turn_number}: {escape(event.stack_id)} skipped"


def _counterattack_status(counterattack: AttackDamageEventData | None) -> str:
    if counterattack is None:
        return ""
    return (
        f"; counterattack: {counterattack.final_damage} damage, "
        f"{counterattack.creatures_killed} killed, "
        f"{counterattack.defender_count_after} left"
    )


def _counterattack_html(counterattack: AttackDamageEventData | None) -> str:
    if counterattack is None:
        return ""
    return (
        '<span class="counterattack-detail">'
        f"Counterattack: {counterattack.final_damage} damage, "
        f"{counterattack.creatures_killed} killed, "
        f"{counterattack.defender_count_after} left"
        "</span>"
    )


def _load_nicegui() -> Any:
    try:
        return import_module("nicegui")
    except ModuleNotFoundError as exc:
        msg = 'NiceGUI is required for the combat replay view. Install it with: pip install -e ".[view]"'
        raise RuntimeError(msg) from exc


if __name__ == "__main__":
    main()
