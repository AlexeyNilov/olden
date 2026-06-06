from pathlib import Path

from olden.battlefield_view.replay_app import (
    DEFAULT_BATTLE_INITIAL_STATE_PATH,
    DEFAULT_COMBAT_LOG_PATH,
    ReplayController,
    _build_page,
    load_default_replay_frames,
)


def test_load_default_replay_frames_uses_demo_battle_and_demo_movement_log():
    frames = load_default_replay_frames()

    assert frames[0].battle.occupancy.unit_at(DEFAULT_PLAYER_START) == "player-esquire"
    assert frames[-1].battle.occupancy.coordinates_for("enemy-esquire")
    assert DEFAULT_BATTLE_INITIAL_STATE_PATH.name == "demo_battle.yaml"
    assert DEFAULT_COMBAT_LOG_PATH.name == "demo_movement_log.yaml"


def test_replay_controller_advances_frames_and_updates_svg():
    svg_container = FakeContainer()
    status_label = FakeLabel()
    timer = FakeTimer()
    controller = ReplayController(
        frames=load_default_replay_frames(),
        svg_container=svg_container,
        status_label=status_label,
        timer=timer,
        delay_seconds=1.5,
        unit_image_directory=Path("missing-images"),
    )

    controller.start()
    controller.advance()

    assert timer.active
    assert timer.interval == 1.5
    assert svg_container.html_updates[-1].count("<polygon ") == 137
    assert "Frame 2 /" in status_label.text


def test_replay_controller_delay_change_updates_timer_interval():
    controller = ReplayController(
        frames=load_default_replay_frames(),
        svg_container=FakeContainer(),
        status_label=FakeLabel(),
        timer=FakeTimer(),
        delay_seconds=1.5,
        unit_image_directory=Path("missing-images"),
    )

    controller.set_delay(0.25)

    assert controller.timer.interval == 0.25


def test_build_page_sets_initial_delay_and_registers_controls():
    ui = FakeUi()

    _build_page(ui, load_default_replay_frames(), delay_seconds=2.0, unit_image_directory=Path("missing-images"))

    assert ui.timer_obj.interval == 2.0
    assert ui.timer_obj.active is False
    assert "Frame 1 /" in ui.label_obj.text
    assert ui.buttons == ["Play", "Pause", "Restart", "Previous", "Next"]


DEFAULT_PLAYER_START = next(iter(load_default_replay_frames()[0].battle.occupancy.coordinates_for("player-esquire")))


class FakeTimer:
    def __init__(self) -> None:
        self.interval: float | None = None
        self.active = False

    def activate(self) -> None:
        self.active = True

    def deactivate(self) -> None:
        self.active = False


class FakeContainer:
    def __init__(self) -> None:
        self.html_updates: list[str] = []

    def set_content(self, content: str) -> None:
        self.html_updates.append(content)

    def classes(self, classes: str) -> "FakeContainer":
        return self


class FakeLabel:
    def __init__(self) -> None:
        self.text = ""

    def set_text(self, text: str) -> None:
        self.text = text


class FakeUi:
    def __init__(self) -> None:
        self.timer_obj = FakeTimer()
        self.label_obj = FakeLabel()
        self.svg_container = FakeContainer()
        self.buttons: list[str] = []

    def page_title(self, title: str) -> None:
        pass

    def add_css(self, css: str) -> None:
        pass

    def column(self) -> "FakeElement":
        return FakeElement()

    def row(self) -> "FakeElement":
        return FakeElement()

    def label(self, text: str) -> FakeLabel:
        self.label_obj.set_text(text)
        return self.label_obj

    def html(self, content: str, *, sanitize: bool = True) -> FakeContainer:
        self.svg_container.set_content(content)
        return self.svg_container

    def button(self, text: str, on_click: object) -> "FakeElement":
        self.buttons.append(text)
        return FakeElement()

    def number(self, label: str, value: float, min: float, max: float, step: float, on_change: object) -> "FakeElement":
        return FakeElement()

    def timer(self, interval: float, callback: object, active: bool = True) -> FakeTimer:
        self.timer_obj.interval = interval
        self.timer_obj.active = active
        return self.timer_obj


class FakeElement:
    def classes(self, classes: str) -> "FakeElement":
        return self

    def props(self, props: str) -> "FakeElement":
        return self

    def __enter__(self) -> "FakeElement":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        pass
