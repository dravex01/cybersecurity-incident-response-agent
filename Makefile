.PHONY: install ingest run test lint evaluate load-test docker-build docker-up docker-down

install:
	python -m pip install -e ".[dev]"

ingest:
	python -m app.rag.ingestion

run:
	python -m streamlit run app/ui/streamlit_app.py

test:
	python -m pytest

lint:
	python -m ruff check .

evaluate:
	python -m evaluation.evaluate

load-test:
	python -m load_tests.load_test --requests 100

docker-build:
	docker build -t cybersecurity-incident-response-agent .

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

