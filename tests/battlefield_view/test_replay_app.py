from pathlib import Path

from olden.battlefield_view.replay_app import (
    DEFAULT_BATTLE_INITIAL_STATE_PATH,
    DEFAULT_COMBAT_LOG_PATH,
    DEFAULT_REPLAY_PORT,
    ReplayController,
    _build_page,
    load_default_replay_frames,
)
from olden.combat.combat_log import UnitAttackedEvent


def test_load_default_replay_frames_uses_demo_battle_and_demo_combat_log():
    frames = load_default_replay_frames()

    assert frames[0].battle.occupancy.unit_at(DEFAULT_PLAYER_START) == "player-esquire"
    assert any(isinstance(frame.event, UnitAttackedEvent) for frame in frames)
    assert DEFAULT_BATTLE_INITIAL_STATE_PATH.name == "demo_battle.yaml"
    assert DEFAULT_COMBAT_LOG_PATH.name == "demo_combat_log.yaml"
    assert DEFAULT_REPLAY_PORT == 8081


def test_replay_controller_advances_frames_and_updates_svg():
    svg_container = FakeContainer()
    log_container = FakeContainer()
    status_label = FakeLabel()
    timer = FakeTimer()
    controller = ReplayController(
        frames=load_default_replay_frames(),
        svg_container=svg_container,
        log_container=log_container,
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
    assert 'class="combat-log-entry active"' in log_container.html_updates[-1]
    assert "Frame 2 /" in status_label.text


def test_replay_controller_formats_attack_events_in_status_and_combat_log():
    frames = load_default_replay_frames()
    first_attack_index = next(index for index, frame in enumerate(frames) if isinstance(frame.event, UnitAttackedEvent))
    svg_container = FakeContainer()
    log_container = FakeContainer()
    status_label = FakeLabel()
    controller = ReplayController(
        frames=frames,
        svg_container=svg_container,
        log_container=log_container,
        status_label=status_label,
        timer=FakeTimer(),
        delay_seconds=1.5,
        unit_image_directory=Path("missing-images"),
    )

    controller.current_index = first_attack_index
    controller.render_current_frame()

    assert "attacked" in status_label.text
    assert "damage" in status_label.text
    assert "counterattack" in status_label.text
    assert "player-esquire attacked enemy-esquire" in log_container.html_updates[-1]
    assert "Counterattack:" in log_container.html_updates[-1]
    assert "; counterattack:" not in log_container.html_updates[-1]


def test_replay_controller_delay_change_updates_timer_interval():
    controller = ReplayController(
        frames=load_default_replay_frames(),
        svg_container=FakeContainer(),
        log_container=FakeContainer(),
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
    assert ui.log_container.html_updates[-1].count("combat-log-entry") >= 1
    assert ui.buttons == ["Play", "Pause", "Restart", "Previous", "Next"]


def test_build_page_applies_high_contrast_delay_input_and_scrollable_log_styles():
    ui = FakeUi()

    _build_page(ui, load_default_replay_frames(), delay_seconds=2.0, unit_image_directory=Path("missing-images"))

    assert ".replay-delay-input .q-field__label" in ui.css
    assert ".replay-delay-input .q-field__native" in ui.css
    assert ".replay-delay-input .q-field__control" in ui.css
    assert "#f7f0d0" in ui.css
    assert "#1f2a44" in ui.css
    assert ".combat-log-panel" in ui.css
    assert "flex: 0 1 auto" in ui.css
    assert "overflow-y: auto" in ui.css
    assert "replay-delay-input" in ui.number_element.class_values
    assert "combat-log-panel" in ui.html_elements[-1].class_values


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
        self.class_values: list[str] = []

    def set_content(self, content: str) -> None:
        self.html_updates.append(content)

    def classes(self, classes: str) -> "FakeContainer":
        self.class_values.append(classes)
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
        self.log_container = FakeContainer()
        self.number_element = FakeElement()
        self.buttons: list[str] = []
        self.css = ""
        self.html_calls = 0
        self.html_updates: list[str] = []
        self.html_elements: list[FakeContainer] = []

    def page_title(self, title: str) -> None:
        pass

    def add_css(self, css: str) -> None:
        self.css += css

    def column(self) -> "FakeElement":
        return FakeElement()

    def row(self) -> "FakeElement":
        return FakeElement()

    def label(self, text: str) -> FakeLabel:
        self.label_obj.set_text(text)
        return self.label_obj

    def html(self, content: str, *, sanitize: bool = True) -> FakeContainer:
        self.html_calls += 1
        container = self.svg_container if self.html_calls == 1 else self.log_container
        container.set_content(content)
        self.html_updates.append(content)
        self.html_elements.append(container)
        return container

    def button(self, text: str, on_click: object) -> "FakeElement":
        self.buttons.append(text)
        return FakeElement()

    def number(self, label: str, value: float, min: float, max: float, step: float, on_change: object) -> "FakeElement":
        return self.number_element

    def timer(self, interval: float, callback: object, active: bool = True) -> FakeTimer:
        self.timer_obj.interval = interval
        self.timer_obj.active = active
        return self.timer_obj


class FakeElement:
    def __init__(self) -> None:
        self.class_values: list[str] = []
        self.prop_values: list[str] = []

    def classes(self, classes: str) -> "FakeElement":
        self.class_values.append(classes)
        return self

    def props(self, props: str) -> "FakeElement":
        self.prop_values.append(props)
        return self

    def __enter__(self) -> "FakeElement":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        pass
