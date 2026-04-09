.PHONY: up down build migrate shell logs restart

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build --no-cache

migrate:
	docker compose run --rm migrate

shell-bot:
	docker compose exec bot bash

shell-db:
	docker compose exec db psql -U avtoban -d avtoban

logs:
	docker compose logs -f bot

logs-all:
	docker compose logs -f

restart:
	docker compose restart bot

dev:
	docker compose up -d db redis
	python -m app.main

migrate-local:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(msg)"
