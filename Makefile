.PHONY: up down api

up:
	docker compose up -d --build

down:
	docker compose down

api:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
