.ONESHELL:

lint:
	prospector

mypy:
	mypy famapy

test:
	python -m pytest -sv
