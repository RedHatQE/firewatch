#!/usr/bin/env bash
# Replay firewatch against one completed Prow job (Phase 1 of openshift-ci validation).
# Prerequisites: development/env.list (see env.list.example). JIRA_TOKEN may be set there or in repo-root .env.
#
# Phase 2 (rehearsal): use fork https://github.com/amp-rh/openshift-release -- push a branch, open a PR to
# openshift/release, then comment on the PR:
#   /pj-rehearse periodic-ci-RedHatQE-interop-testing-master-ibm-fusion-access-operator-ocp4.21-lp-interop-ibm-fusion-access-operator-ipi-ocp421
# That periodic uses workflow firewatch-ipi-aws (post: firewatch-report-issues). Rehearsal uses the
# firewatch image pinned in openshift/release, not your local firewatch branch, unless you bump the image there.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ENV_FILE="${ROOT}/development/env.list"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing ${ENV_FILE}. Copy development/env.list.example and set JIRA_TOKEN." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [[ -f "${ROOT}/.env" ]]; then
  while IFS= read -r line; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    case "$line" in
      JIRA_TOKEN=*)
        if [[ -z "${JIRA_TOKEN:-}" ]]; then
          v="${line#JIRA_TOKEN=}"
          v="${v#\"}"
          v="${v%\"}"
          v="${v#\'}"
          v="${v%\'}"
          export JIRA_TOKEN="$v"
        fi
        ;;
      JIRA_EMAIL=*)
        if [[ -z "${JIRA_EMAIL:-}" ]]; then
          v="${line#JIRA_EMAIL=}"
          v="${v#\"}"
          v="${v%\"}"
          export JIRA_EMAIL="$v"
        fi
        ;;
    esac
  done < "${ROOT}/.env"
fi

if [[ -z "${JIRA_TOKEN:-}" ]]; then
  echo "JIRA_TOKEN is empty. Set it in development/env.list or as JIRA_TOKEN= in repo-root .env." >&2
  exit 1
fi

if [[ -z "${JIRA_SERVER_URL:-}" ]]; then
  echo "JIRA_SERVER_URL is required (see env.list.example)." >&2
  exit 1
fi

echo "${JIRA_TOKEN}" > /tmp/firewatch-smoke-token
uv sync -q
GEN_ARGS=(
  firewatch jira-config-gen
  --token-path /tmp/firewatch-smoke-token
  --server-url "${JIRA_SERVER_URL}"
  --template-path "${ROOT}/src/templates/jira.config.j2"
)
if [[ -n "${JIRA_EMAIL:-}" ]]; then
  GEN_ARGS+=(--email "${JIRA_EMAIL}")
fi
uv run "${GEN_ARGS[@]}"
rm -f /tmp/firewatch-smoke-token

uv run python -c "
import json
with open('/tmp/jira.config') as f:
    cfg = json.load(f)
cfg.pop('proxies', None)
with open('/tmp/jira.config', 'w') as f:
    json.dump(cfg, f, indent=2)
"

export FIREWATCH_DEFAULT_JIRA_PROJECT="${FIREWATCH_DEFAULT_JIRA_PROJECT:?}"
export FIREWATCH_CONFIG="${FIREWATCH_CONFIG:?}"

exec uv run firewatch report \
  --keep-job-dir \
  --jira-config-path /tmp/jira.config
