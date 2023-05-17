pre-commit:
	pre-commit run --all-files

test:
	tox

dev-environment:
	python -m venv venv
	source venv/bin/activate
	pip install tox pre-commit
	pip install -e .

docker-build:
	docker build -t firewatch .

docker-run:
	docker run -it firewatch bash

build-run: docker-build docker-run
