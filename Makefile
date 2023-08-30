IMAGE_BUILD_CMD=$(shell which podman 2>/dev/null || which docker)

pre-commit:
	pre-commit run --all-files

test:
	tox

commit: pre-commit test

dev-environment:
	python3 -m pip install pip poetry --upgrade
	poetry install

build:
	$(IMAGE_BUILD_CMD) build -t firewatch .

test:
	$(IMAGE_BUILD_CMD) run -it --env-file development/env.list --entrypoint /bin/bash firewatch /development/test.sh

run:
	$(IMAGE_BUILD_CMD) run -it --env-file development/env.list --entrypoint /bin/bash firewatch

build-run: docker-build docker-run

build-test: docker-build docker-test
