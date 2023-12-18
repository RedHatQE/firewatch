FROM docker.io/library/python:3.12-slim

COPY pyproject.toml poetry.lock README.md /firewatch/
COPY cli /firewatch/cli/
COPY --chmod=0755 development /development

WORKDIR /firewatch

ENV POETRY_HOME=/firewatch
ENV PATH="/firewatch/bin:$PATH"

RUN python3 -m pip install pip poetry --upgrade \
    && poetry config cache-dir /firewatch \
    && poetry config virtualenvs.in-project true \
    && poetry config installer.max-workers 10 \
    && poetry install \
    && printf '#!/bin/bash \n poetry run firewatch $@' > /usr/bin/firewatch \
    && chmod +x /usr/bin/firewatch

COPY --from=zricethezav/gitleaks:v7.6.1 /usr/bin/gitleaks /usr/bin/gitleaks

ENTRYPOINT ["firewatch"]
