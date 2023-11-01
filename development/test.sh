#!/bin/bash

# Build Jira config
echo "${JIRA_TOKEN}" > /tmp/token
firewatch jira-config-gen --token-path /tmp/token --server-url "${JIRA_SERVER_URL}"

# Execute Firewatch
firewatch report
