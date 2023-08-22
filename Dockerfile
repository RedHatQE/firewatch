FROM docker.io/library/python:3.11

## Copy firewatch package into /firewatch folder
#RUN mkdir /firewatch
#COPY . /firewatch/
#
## Install firewatch
#RUN pip install --upgrade pip
#RUN pip install /firewatch tox
#
## Copy the Jira config template to /templates
#RUN mkdir /templates
#COPY cli/templates/* /templates/
#
## Add permissions
#RUN chgrp -R 0 /tmp && \
#    chmod -R g=u /tmp
#
#RUN chgrp -R 0 /firewatch && \
#    chmod -R g=u /firewatch
#
#RUN chgrp -R 0 /templates && \
#    chmod -R g=u /templates
#
#CMD ["/bin/bash"]


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