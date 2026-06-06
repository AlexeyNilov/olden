import argparse
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_DIRECTORY = PROJECT_ROOT / ".run"


@dataclass(frozen=True, slots=True)
class ViewApp:
    name: str
    module: str
    url: str

    @property
    def pid_path(self) -> Path:
        return RUN_DIRECTORY / f"{self.name}.pid"

    @property
    def log_path(self) -> Path:
        return RUN_DIRECTORY / f"{self.name}.log"


VIEW_APPS = {
    "static": ViewApp(
        name="static",
        module="olden.battlefield_view.static",
        url="http://localhost:8082",
    ),
    "replay": ViewApp(
        name="replay",
        module="olden.battlefield_view.replay_app",
        url="http://localhost:8081",
    ),
}


def main() -> None:
    args = _parse_args()
    app = VIEW_APPS[args.app]
    if args.command == "start":
        start(app)
    elif args.command == "stop":
        stop(app)
    elif args.command == "restart":
        restart(app)
    elif args.command == "status":
        status(app)


def start(app: ViewApp) -> None:
    RUN_DIRECTORY.mkdir(exist_ok=True)
    pid = _read_pid(app.pid_path)
    if pid is not None and _is_running(pid):
        print(f"{app.name} view already running at {app.url} (pid {pid})")
        return

    log_file = app.log_path.open("a", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, "-m", app.module],
        cwd=PROJECT_ROOT,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    app.pid_path.write_text(str(process.pid), encoding="utf-8")
    print(f"Started {app.name} view at {app.url} (pid {process.pid}, log {app.log_path})")


def stop(app: ViewApp) -> None:
    pid = _read_pid(app.pid_path)
    if pid is None:
        print(f"{app.name} view is not managed by {app.pid_path}")
        return
    if not _is_running(pid):
        app.pid_path.unlink(missing_ok=True)
        print(f"{app.name} view was not running")
        return

    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if not _is_running(pid):
            app.pid_path.unlink(missing_ok=True)
            print(f"Stopped {app.name} view")
            return
        time.sleep(0.1)

    print(f"{app.name} view did not stop within 5 seconds (pid {pid})")


def restart(app: ViewApp) -> None:
    stop(app)
    start(app)


def status(app: ViewApp) -> None:
    pid = _read_pid(app.pid_path)
    if pid is not None and _is_running(pid):
        print(f"{app.name} view running at {app.url} (pid {pid}, log {app.log_path})")
        return
    print(f"{app.name} view stopped")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage local Olden browser views.")
    parser.add_argument("command", choices=("start", "stop", "restart", "status"))
    parser.add_argument("app", choices=tuple(VIEW_APPS))
    return parser.parse_args()


def _read_pid(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        return None


def _is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


if __name__ == "__main__":
    main()
