FROM docker/dev-environments-default:stable-1

# Copy in required files
COPY . .

# Update and install required packages
RUN apt update -y && apt upgrade -y \
    && apt install -y build-essential python3-pip software-properties-common\
    && printf '#!/bin/bash \n python3 $@' > /usr/bin/python \
    && chmod +x /usr/bin/python \
    && python -m pip install pip poetry tox pre-commit --upgrade \
    && poetry config cache-dir /firewatch \
    && poetry config virtualenvs.in-project true \
    && poetry config installer.max-workers 10 \
    && poetry install \
    && printf '#!/bin/bash \n poetry run firewatch $@' > /usr/bin/firewatch \
    && chmod +x /usr/bin/firewatch
