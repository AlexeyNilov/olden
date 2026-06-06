from collections.abc import Sequence
from html import escape
from importlib import import_module
from pathlib import Path
from typing import Any

from olden.battlefield_view.model import build_battlefield_view_for_battle
from olden.battlefield_view.svg import (
    DEFAULT_UNIT_IMAGE_DIRECTORY,
    register_unit_image_static_files,
    render_battlefield_svg,
)
from olden.combat.battle_setup import load_battle_initial_state_file
from olden.combat.combat_log import UnitMovedEvent, load_combat_log_file
from olden.combat.combat_replay import CombatReplayFrame, build_combat_replay_frames
from olden.unit_data.packaged import load_packaged_unit_catalog

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BATTLE_INITIAL_STATE_PATH = PROJECT_ROOT / "data" / "demo_battle.yaml"
DEFAULT_COMBAT_LOG_PATH = PROJECT_ROOT / "data" / "demo_movement_log.yaml"
DEFAULT_REPLAY_DELAY_SECONDS = 1.0
DEFAULT_REPLAY_PORT = 8081


class ReplayController:
    def __init__(
        self,
        frames: Sequence[CombatReplayFrame],
        svg_container: Any,
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
        self.status_label.set_text(_frame_status(frame))


def main() -> None:
    run_combat_replay_view()


def run_combat_replay_view(
    initial_state_path: Path = DEFAULT_BATTLE_INITIAL_STATE_PATH,
    combat_log_path: Path = DEFAULT_COMBAT_LOG_PATH,
    delay_seconds: float = DEFAULT_REPLAY_DELAY_SECONDS,
    port: int = DEFAULT_REPLAY_PORT,
) -> None:
    nicegui = _load_nicegui()
    ui = getattr(nicegui, "ui")
    frames = load_replay_frames(initial_state_path, combat_log_path)
    register_unit_image_static_files(getattr(nicegui, "app"), DEFAULT_UNIT_IMAGE_DIRECTORY)
    _build_page(ui, frames, delay_seconds, DEFAULT_UNIT_IMAGE_DIRECTORY)
    ui.run(title="Olden Combat Replay", reload=False, show=False, port=port)


def load_default_replay_frames() -> tuple[CombatReplayFrame, ...]:
    return load_replay_frames(DEFAULT_BATTLE_INITIAL_STATE_PATH, DEFAULT_COMBAT_LOG_PATH)


def load_replay_frames(initial_state_path: Path, combat_log_path: Path) -> tuple[CombatReplayFrame, ...]:
    battle = load_battle_initial_state_file(initial_state_path, load_packaged_unit_catalog())
    combat_log = load_combat_log_file(combat_log_path)
    return build_combat_replay_frames(battle, combat_log)


def _build_page(
    ui: Any,
    frames: Sequence[CombatReplayFrame],
    delay_seconds: float = DEFAULT_REPLAY_DELAY_SECONDS,
    unit_image_directory: Path = DEFAULT_UNIT_IMAGE_DIRECTORY,
) -> ReplayController:
    ui.page_title("Olden Combat Replay")
    ui.add_css("body { background: #10131f; color: #f7f0d0; }")
    with ui.column().classes("w-full items-center q-pa-md"):
        status_label = ui.label("")
        svg_container = ui.html("", sanitize=False).classes("battlefield-view")
        timer_callback = _ReplayTimerCallback()
        timer = ui.timer(delay_seconds, timer_callback, active=False)
        controller = ReplayController(
            frames=frames,
            svg_container=svg_container,
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
            ).props("dense")
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
    return f"{prefix} - event {frame.event.sequence}"


def _load_nicegui() -> Any:
    try:
        return import_module("nicegui")
    except ModuleNotFoundError as exc:
        msg = 'NiceGUI is required for the combat replay view. Install it with: pip install -e ".[view]"'
        raise RuntimeError(msg) from exc


if __name__ == "__main__":
    main()
