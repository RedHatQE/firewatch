#!/bin/bash

# Build Jira config
echo $JIRA_TOKEN > /tmp/token
firewatch jira_config_gen --token_path /tmp/token --server_url $JIRA_SERVER_URL

# Execute Firewatch
firewatch report