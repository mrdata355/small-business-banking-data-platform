.PHONY: build run results test clean

build:
	docker compose build

run:
	docker compose run --rm platform

results:
	docker compose run --rm platform python scripts/show_results.py

test:
	docker compose run --rm platform pytest -q

clean:
	rm -rf runtime .pytest_cache .ruff_cache
