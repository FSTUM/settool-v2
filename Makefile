.PHONY: lint linting test bandit mypy pylint

lint: linting

linting: pylint mypy bandit

test: run_pytests

pylint:
	pylint ./**/*.py

mypy:
	mypy --ignore-missing-imports .

bandit:
	bandit -r . -x .svn,CVS,.bzr,.hg,.git,__pycache__,.tox,.eggs,*.egg,*/lib/*,*venv/,bin,lib64,share,.mypy_cache

run_pytests:
	python3 manage.py test
