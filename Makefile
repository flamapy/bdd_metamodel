.ONESHELL:

lint:
	prospector

mypy:
	mypy flamapy

test:
	python -m pytest -sv
