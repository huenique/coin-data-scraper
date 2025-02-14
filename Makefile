.PHONY: lint

lint:
	ruff check --select I --fix && ruff format

export:
	poetry export --without-hashes --without dev -f requirements.txt -o requirements.txt
