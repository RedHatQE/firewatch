FROM ghcr.io/astral-sh/uv:python3.12-bookworm

COPY pyproject.toml uv.lock README.md /firewatch/
COPY src /firewatch/src/
COPY --chmod=0755 development /development

WORKDIR /firewatch

ENV PATH="/firewatch/bin:$PATH"

COPY dist/*.whl .
RUN uv pip install --system *.whl

ENTRYPOINT ["firewatch"]
