# Firewatch Architecture

## Overview

Firewatch is a Python CLI tool that monitors OpenShift CI job results and automatically
reports failures to Jira. It bridges the gap between CI infrastructure and issue tracking
by parsing test artifacts, matching failures against user-defined rules, and creating
structured Jira issues with full context.

## System Architecture

```text
OpenShift CI (Prow) --> GCS Artifacts --> Firewatch CLI --> Jira API
                                              |
                                              +--> Slack API (optional notifications)
```

1. **Input**: Firewatch reads JUnit XML results and pod logs from GCS artifact storage.
2. **Processing**: The rule engine matches each failure against the user's configuration.
3. **Output**: Matching failures are filed as Jira issues with logs, classifications, and links.

## Key Components

- **CLI (`src/cli.py`)**: Click-based entry point that parses arguments and dispatches commands.
- **Report engine (`src/report/report.py`)**: Core logic for failure detection, rule matching,
  duplicate detection, and Jira issue creation/update.
- **Rule engine (`src/objects/rule.py`, `src/objects/failure_rule.py`)**: Defines how failures
  map to Jira projects, components, priorities, and labels via configurable rules.
- **Jira integration (`src/objects/jira_base.py`)**: Wraps the Jira API client for issue
  creation, commenting, linking, and transition workflows.
- **Escalation (`src/escalation/`)**: Handles Jira-based escalation workflows for unresolved issues.
- **Config generation (`src/jira_config_gen/`)**: Generates firewatch configuration templates.

## Design Decisions

- **Python**: Chosen for its rich ecosystem of CI/testing libraries (`junitparser`, `jira`,
  `google-cloud-storage`) and ease of integration with OpenShift CI step registry.
- **Jira as backend**: Jira is the standard issue tracker in the Red Hat ecosystem, providing
  built-in workflows, permissions, and integrations that teams already use.
- **Rule-based matching**: A declarative configuration model allows teams to customize failure
  routing without modifying code. Rules support wildcards, grouping, and priority ordering.
- **Duplicate detection**: Firewatch uses Jira labels (failure type, step name, job name) to
  detect and comment on existing issues rather than creating duplicates.
