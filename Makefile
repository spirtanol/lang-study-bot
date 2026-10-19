DC_DEV = docker compose -f docker-compose.dev.yml

.PHONY: up down shell migrate db stop ollama-pull ollama-up chat start-scheduler stop-scheduler logs-worker logs-tg-worker start-web stop-web logs-web

MODEL ?= qwen3:4b

up:
	$(DC_DEV) up -d

down:
	$(DC_DEV) down

shell:
	$(DC_DEV) run --rm -it web bash

migrate:
	$(DC_DEV) run --rm web poetry run alembic upgrade head

db:
	$(DC_DEV) exec -it db sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

stop:
	$(DC_DEV) down web scheduler worker telegram-worker rabbitmq

ollama-up:
	$(DC_DEV) up -d ollama

ollama-pull:
	$(DC_DEV) exec ollama ollama pull $(MODEL)

chat:
	$(DC_DEV) run --rm web poetry run python -m app.cli chat

start-scheduler:
	$(DC_DEV) up -d scheduler

stop-scheduler:
	$(DC_DEV) down scheduler worker telegram-worker

logs-worker:
	$(DC_DEV) logs worker -f

logs-tg-worker:
	$(DC_DEV) logs telegram-worker -f

start-web:
	$(DC_DEV) up -d web

stop-web:
	$(DC_DEV) down web

logs-web:
	$(DC_DEV) logs web -f