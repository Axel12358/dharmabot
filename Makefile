.PHONY: install lint test run loop fecha org clean

VENV := .venv
PY := $(VENV)/bin/python

install:               ## Crea venv e instala deps + dev con uv
	uv venv $(VENV)
	$(PY) -m pip install -e '.[dev]'

lint:                  ## Lint + formato (ruff)
	$(PY) -m ruff check core/ --fix || true
	$(PY) -m ruff format core/ tests/ || true

test:                  ## Tests puros sin red
	$(PY) -m pytest -q --no-header -W ignore tests/

run:                   ## Loop principal de enriquecimiento
	./run_loop_completar.sh

loop:                  ## Igual que run (alias)
	$(PY) run_loop.py

fecha:                 ## Pase de fechas FB (og:description)
	$(PY) recuperar_fechas.py

org:                   ## Pase offline org/email desde caches
	$(PY) empujar_org_email.py

clean:                 ## Limpia artefactos locales
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -f *.log *.err *.out