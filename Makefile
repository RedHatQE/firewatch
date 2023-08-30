pre-commit:
	pre-commit run --all-files

test:
	tox

commit: pre-commit test

dev-environment:
	python -m venv venv
	. venv/bin/activate
	pip install tox pre-commit
	pip install -e .

docker-build:
	docker build -t firewatch .

docker-test:
	docker run -it --env-file development/env.list --entrypoint /bin/bash firewatch /development/test.sh

docker-run:
	docker run -it --env-file development/env.list --entrypoint /bin/bash firewatch

docker-build-run: docker-build docker-run

docker-build-test: docker-build docker-test
