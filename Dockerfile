FROM docker.io/library/python:3.11

COPY pyproject.toml poetry.lock README.md /firewatch/
COPY cli /firewatch/cli/

WORKDIR /firewatch

ENV POETRY_HOME=/firewatch
ENV PATH="/firewatch/bin:$PATH"

RUN python3 -m pip install pip poetry --upgrade \
    && poetry config cache-dir /openshift-cli-installer \
    && poetry config virtualenvs.in-project true \
    && poetry config installer.max-workers 10 \
    && poetry install


ENTRYPOINT ["poetry", "run", "firewatch"]
