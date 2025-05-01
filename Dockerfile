FROM ghcr.io/astral-sh/uv:python3.12-bookworm

COPY pyproject.toml uv.lock README.md LICENSE /firewatch/
COPY src /firewatch/src/
COPY --chmod=0755 development /development

WORKDIR /firewatch

ENV PATH="/firewatch/bin:$PATH"

RUN uv sync \
    && uv build --wheel -o . \
    && uv pip install --system *.whl

ENTRYPOINT ["firewatch"]
