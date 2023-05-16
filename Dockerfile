FROM docker.io/library/python:3.11

# Copy firewatch package into /firewatch folder
RUN mkdir /firewatch
COPY . /firewatch/

# Install firewatch
RUN pip install --upgrade pip
RUN pip install /firewatch

# Copy the Jira config template to /templates
RUN mkdir /templates
COPY cli/templates/* /templates/

# Add permissions
RUN chgrp -R 0 /tmp && \
    chmod -R g=u /tmp

RUN chgrp -R 0 /firewatch && \
    chmod -R g=u /firewatch

RUN chgrp -R 0 /templates && \
    chmod -R g=u /templates

CMD ["tail", "-f", "/dev/null"]
#ENTRYPOINT ["firewatch", "report"]
