# Firewatch Threat Model

## Overview

Firewatch processes CI job artifacts and interacts with external services (Jira, GCS, Slack).
This document outlines the security considerations, trust boundaries, and mitigations in place.

## Trust Boundaries

1. **OpenShift CI environment** - Firewatch runs as a post-step in Prow jobs with access to
   job artifacts and CI secrets.
2. **GCS artifact storage** - Read-only access to JUnit XML results and pod logs.
3. **Jira API** - Authenticated write access for creating/updating issues and comments.
4. **Slack API** - Optional authenticated access for sending notifications.

## Data Flow

```text
GCS (artifacts) --[read]--> Firewatch --[write]--> Jira (issues, comments, attachments)
                                |
                                +--[write]--> Slack (notifications, optional)
```

## Authentication and Credentials

- **Jira API token**: Read from a file path (`FIREWATCH_JIRA_API_TOKEN_PATH`), typically
  mounted as a Kubernetes secret in CI. Never stored in source code or configuration files.
- **GCS credentials**: Provided by the CI environment's service account. No user-managed keys.
- **Slack token**: Optional, provided via environment variable or secret mount.

## Threats and Mitigations

| Threat | Mitigation |
|--------|------------|
| Credentials committed to source | `detect-secrets` in pre-commit hooks scans for leaked tokens |
| Jira token exposure in logs | Token is read from file, not passed as CLI argument |
| Malicious JUnit XML injection | `junitparser` processes only well-formed XML; no code execution |
| Unauthorized Jira access | Jira permissions are scoped per-project via the API user's role |
| CI artifact tampering | GCS access uses authenticated service accounts with audit logging |

## Security Tooling

- **detect-secrets**: Pre-commit hook that scans for hardcoded secrets and API keys.
- **ruff with flake8-bandit (S) rules**: Static analysis for common security anti-patterns.
- **pre-commit**: Enforces all security checks before code is committed.

## Scope Limitations

Firewatch does not handle user authentication directly. It relies on the CI platform
(OpenShift/Prow) for identity, secret management, and network-level access controls.
