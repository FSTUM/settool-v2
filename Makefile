.PHONY: lint test bandit mypy pylint

lint: pylint mypy bandit

pylint:
	pylint ./**/*.py

mypy:
	mypy --ignore-missing-imports .

bandit:
	bandit -r . -x .svn,CVS,.bzr,.hg,.git,__pycache__,.tox,.eggs,*.egg,*/lib/*,*venv/,bin,lib64,share,.mypy_cache

test:
	python3 manage.py test
