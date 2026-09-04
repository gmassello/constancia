.PHONY: dev test lint demo call smoke smoke-stt smoke-tts models db schema seed

dev:
	uv run uvicorn app.main:app --reload --port 8000

test:
	uv run pytest -q

lint:
	uv run ruff check .

demo:
	MEMORY=$(MEMORY) uv run python scripts/demo.py

call:
	uv run python scripts/place_call.py $(PHONE)

smoke:
	uv run python scripts/test_outbound.py $(PHONE)

smoke-stt:
	uv run python scripts/smoke_stt.py

smoke-tts:
	uv run python scripts/smoke_tts.py

models:
	uv run python scripts/list_models.py

db:
	docker-compose up -d db

schema:
	uv run python -m app.db

seed:
	uv run python scripts/seed.py
