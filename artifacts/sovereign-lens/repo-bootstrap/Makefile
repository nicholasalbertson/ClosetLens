.PHONY: install test run verify

install:
	python -m pip install -e ".[dev]"

test:
	pytest -q

run:
	uvicorn sovereign_closet.api:app --reload

verify:
	pytest -q
