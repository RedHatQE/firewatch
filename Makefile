IMAGE_BUILD_CMD=$(shell which podman 2>/dev/null || which docker)

pre-commit:
	pre-commit run --all-files

test:
	tox

commit: pre-commit test

dev-environment:
	python3 -m pip install pip poetry --upgrade
	poetry install

container-build:
	$(IMAGE_BUILD_CMD) build -t firewatch .

container-test:
	$(IMAGE_BUILD_CMD) run -it --env-file development/env.list --entrypoint /bin/bash firewatch /development/test.sh

container-run:
	$(IMAGE_BUILD_CMD) run -it --env-file development/env.list --entrypoint /bin/bash firewatch

container-build-run: container-build container-run

container-build-test: container-build container-test
