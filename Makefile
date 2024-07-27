.ONESHELL:

lint:
	prospector

mypy:
	mypy flamapy --no-namespace-packages

test:
	python -m pytest -sv
