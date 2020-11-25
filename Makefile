.PHONY: lint test bandit mypy pylint

lint: pylint mypy bandit

pylint:
	pylint ./**/*.py

mypy:
	mypy --ignore-missing-imports .

bandit:
	bandit -r .

test:
	python3 manage.py test
