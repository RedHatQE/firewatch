# ADR 0001: Use Jira for CI Failure Tracking

## Status

Accepted (Retroactive)

> **Note:** This ADR documents an existing decision made at project inception.

## Context

OpenShift CI (Prow) runs thousands of jobs daily. When jobs fail, engineers need a
structured way to track, triage, and resolve failures. Without automated tracking,
failures are noticed late, duplicates pile up, and historical context is lost.

We evaluated several options for tracking CI failures:

- **GitHub Issues**: Lightweight but lacks the workflow customization, security levels,
  and cross-project linking that large engineering organizations require.
- **Custom database**: Maximum flexibility but high maintenance burden and no existing
  integrations with team workflows.
- **Jira**: Already the standard issue tracker across Red Hat engineering teams, with
  mature APIs, configurable workflows, and existing team dashboards.

## Decision

We will use Jira as the backend for tracking CI failures. Firewatch will create and
update Jira issues via the Jira REST API, using configurable rules to route failures
to the appropriate projects, components, and assignees.

## Consequences

### Positive

- Teams use their existing Jira workflows and dashboards without adopting new tools.
- Rich metadata support: components, epics, priorities, security levels, and custom fields.
- Built-in duplicate detection via Jira labels and JQL queries.
- Audit trail through Jira's native comment and change history.

### Negative

- Requires Jira API credentials to be provisioned and managed in CI environments.
- Jira API rate limits may constrain high-volume failure reporting scenarios.
- Adds a runtime dependency on Jira server availability.

### Mitigations

- API tokens are stored as CI secrets and never committed to source control.
- Firewatch batches operations and deduplicates before making API calls.
- Failures to reach Jira are logged but do not block the CI pipeline.
