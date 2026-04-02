#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${FIREWATCH_JIRA_VAULT_PATH:-}" ]]; then
  echo "FIREWATCH_JIRA_VAULT_PATH is not set (KV path to the firewatch-tool Jira secret)." >&2
  exit 1
fi

EMAIL_FIELD="${FIREWATCH_JIRA_VAULT_EMAIL_FIELD:-email}"
TOKEN_FIELD="${FIREWATCH_JIRA_VAULT_TOKEN_FIELD:-token}"

JSON=$(vault kv get -format=json "${FIREWATCH_JIRA_VAULT_PATH}")

export JIRA_EMAIL
export JIRA_TOKEN
JIRA_EMAIL=$(echo "${JSON}" | jq -r --arg k "${EMAIL_FIELD}" '.data.data[$k] // .data[$k] // empty')
JIRA_TOKEN=$(echo "${JSON}" | jq -r --arg k "${TOKEN_FIELD}" '.data.data[$k] // .data[$k] // empty')

if [[ -z "${JIRA_EMAIL}" || -z "${JIRA_TOKEN}" ]]; then
  echo "Could not read email/token from Vault at ${FIREWATCH_JIRA_VAULT_PATH}." >&2
  echo "Set FIREWATCH_JIRA_VAULT_EMAIL_FIELD / FIREWATCH_JIRA_VAULT_TOKEN_FIELD if your KV keys differ." >&2
  exit 1
fi
