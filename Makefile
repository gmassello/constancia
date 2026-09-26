.PHONY: dev take test lint check-numbers demo call smoke smoke-stt smoke-tts smoke-call smoke-analysis smoke-keyphrases smoke-jev models db schema seed web web-dev fixtures

dev:
	uv run uvicorn app.main:app --reload --port 8001

take:
	uv run uvicorn app.main:app --port 8001

test:
	uv run pytest -q

lint:
	uv run ruff check .

check-numbers:
	uv run python scripts/check_numbers.py

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

smoke-call:
	uv run python scripts/smoke_call.py

smoke-analysis:
	uv run python scripts/smoke_analysis.py $(URL)

smoke-keyphrases:
	uv run python scripts/smoke_keyphrases.py $(URL)

smoke-jev:
	uv run python scripts/smoke_jev.py

models:
	uv run python scripts/list_models.py

db:
	docker-compose up -d db

schema:
	uv run python -m app.db

seed:
	uv run python scripts/seed.py

web:
	cd web && pnpm install --frozen-lockfile && pnpm build

web-dev:
	cd web && pnpm dev

fixtures:
	uv run python scripts/record.py
