#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

TESTS=(
  "tests/unittests/functions/report/test_firewatch_functions_report_jira_graceful_failures.py::test_report_success_logs_warning_when_create_issue_raises_jira_error"
  "tests/unittests/functions/report/test_firewatch_functions_report_jira_graceful_failures.py::test_report_success_continues_next_rule_after_create_issue_failure"
)

echo "RED: strip graceful try/except from report_success"
python3 scripts/toggle_report_success_graceful.py strip
set +e
uv run pytest "${TESTS[@]}" -v --tb=short
RED_EXIT=$?
set -e
python3 scripts/toggle_report_success_graceful.py restore
if [[ "${RED_EXIT}" -eq 0 ]]; then
  echo "RED phase expected pytest failures but got success" >&2
  exit 1
fi

echo "GREEN: run tests with graceful handler restored"
uv run pytest "${TESTS[@]}" -v --tb=short

echo "OK: RED failed as expected, GREEN passed"
