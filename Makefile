CONTAINER_CMD=$(shell which podman 2>/dev/null || which docker)
TAG ?= latest

pre-commit:
	pre-commit run --all-files

test:
	tox

commit: pre-commit test

dev-environment:
	python3 -m pip install pip poetry --upgrade
	poetry install

container-build:
	$(CONTAINER_CMD) build -t firewatch:$(TAG) .

container-test:
	$(CONTAINER_CMD) run -it --env-file development/env.list --entrypoint /bin/bash firewatch:$(TAG) /development/test.sh

container-run:
	$(CONTAINER_CMD) run -it --env-file development/env.list --entrypoint /bin/bash firewatch:$(TAG)

container-build-run: container-build container-run

container-build-test: container-build container-test
