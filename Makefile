ifeq ($(OS),Windows_NT)
VENV_BIN = .venv/Scripts
EXE = .exe
else
VENV_BIN = .venv/bin
EXE =
endif

PYTHON = $(VENV_BIN)/python$(EXE)
PIP = $(VENV_BIN)/pip$(EXE)
PYTEST = $(VENV_BIN)/pytest$(EXE)
RUFF = $(VENV_BIN)/ruff$(EXE)
MYPY = $(VENV_BIN)/mypy$(EXE)
VIEW_SERVER = scripts/view_server.py

install:
	$(PIP) install -e .[dev]

test:
	$(PYTEST)

lint:
	$(RUFF) check .

mypy:
	$(MYPY) src sample scripts tests

format:
	$(RUFF) format --check .

static-view:
	$(PYTHON) $(VIEW_SERVER) start static

restart-static-view:
	$(PYTHON) $(VIEW_SERVER) restart static

stop-static-view:
	$(PYTHON) $(VIEW_SERVER) stop static

replay-view:
	$(PYTHON) $(VIEW_SERVER) start replay

restart-replay-view:
	$(PYTHON) $(VIEW_SERVER) restart replay

stop-replay-view:
	$(PYTHON) $(VIEW_SERVER) stop replay

view-status:
	$(PYTHON) $(VIEW_SERVER) status static
	$(PYTHON) $(VIEW_SERVER) status replay
