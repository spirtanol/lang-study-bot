DC_FILE ?= docker compose -f docker-compose.dev.yml

.PHONY: up down shell migrate db stop ollama-pull ollama-up chat start-scheduler stop-scheduler logs-worker logs-tg-worker start-web stop-web logs-web dozzle-user

MODEL ?= qwen3:4b

up:
	$(DC_FILE) up -d

down:
	$(DC_FILE) down

shell:
	$(DC_FILE) run --rm -it web bash

migrate:
	$(DC_FILE) run --rm web poetry run alembic upgrade head

db:
	$(DC_FILE) exec -it db sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

stop:
	$(DC_FILE) down web scheduler worker telegram-worker rabbitmq

ollama-up:
	$(DC_FILE) up -d ollama

ollama-pull:
	$(DC_FILE) exec ollama ollama pull $(MODEL)

chat:
	$(DC_FILE) run --rm web poetry run python -m app.cli chat

start-scheduler:
	$(DC_FILE) up -d scheduler

stop-scheduler:
	$(DC_FILE) down scheduler worker telegram-worker

logs-worker:
	$(DC_FILE) logs worker -f

logs-tg-worker:
	$(DC_FILE) logs telegram-worker -f

start-web:
	$(DC_FILE) up -d web

stop-web:
	$(DC_FILE) down web

logs-web:
	$(DC_FILE) logs web -f

dozzle-user:
	@test -n "$(PASSWORD)" || (echo "PASSWORD is required" && exit 1)
	mkdir -p dozzle-data
	docker run --rm amir20/dozzle:v8 generate admin --password "$(PASSWORD)" --name Admin > dozzle-data/users.yml