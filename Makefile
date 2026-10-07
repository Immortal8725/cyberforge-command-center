# Defensive core lifecycle. Requires Docker Compose v2.
COMPOSE ?= docker compose

.PHONY: up down logs ps health config test

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=200

ps:
	$(COMPOSE) ps

health:
	./tests/verify-defensive-core.sh

config:
	$(COMPOSE) config

test:
	python -m pytest zone3-defenses/ml_engine/test_smoke.py
