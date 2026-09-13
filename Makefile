.PHONY: install run report test clean

install:
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

run:
	python3 -m src.pipeline

report:
	python3 -m src.report

test:
	python3 -m pytest -v

clean:
	rm -f warehouse.db logs/*.log data/raw/*.json data/processed/*.csv
