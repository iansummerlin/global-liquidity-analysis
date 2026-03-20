.PHONY: setup test fetch-all update evaluate validate clean-cache

setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

test:
	.venv/bin/python -m pytest tests/ -v

fetch-all:
	.venv/bin/python -c "from data.pipeline import fetch_and_validate, report_sources; d = fetch_and_validate(); print(report_sources(d))"

update:
	.venv/bin/python main.py

evaluate:
	.venv/bin/python main.py evaluate

validate:
	.venv/bin/python -c "from main import validate; import sys; sys.exit(0 if validate() else 1)"

clean-cache:
	rm -rf data/cache/
