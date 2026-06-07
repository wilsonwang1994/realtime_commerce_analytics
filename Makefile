.PHONY: up down build logs generate replay init-db reset-db api worker test lint format smoke

up:
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

generate:
	uv run python sample-data/generate.py

replay:
	APP_KAFKA_BOOTSTRAP_SERVERS=localhost:19092 uv run python sample-data/replay.py --file sample-data/events.jsonl

init-db:
	APP_CLICKHOUSE_HOST=localhost uv run python scripts/init_clickhouse.py

reset-db:
	APP_CLICKHOUSE_HOST=localhost uv run python scripts/reset_clickhouse.py

api:
	APP_CLICKHOUSE_HOST=localhost uv run uvicorn realtime_commerce_analytics.api.main:app --reload --host 0.0.0.0 --port 8000

worker:
	APP_KAFKA_BOOTSTRAP_SERVERS=localhost:19092 APP_CLICKHOUSE_HOST=localhost uv run python -m realtime_commerce_analytics.processor.worker

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

smoke:
	curl -s http://localhost:8000/health && echo
	curl -s http://localhost:8000/metrics?limit=5 && echo
