# firewatch

Thank you for your interest in the firewatch project! Please find some information about the project below. If you are looking for more information, please see the additional documentation below:

- [CLI Usage Guide](docs/cli_usage_guide.md)
- [Configuration Guide](docs/configuration_guide.md)
- [Contribution Guide](docs/contribution_guide.md)

## Features

- Automatically creates Jira issues for failed OpenShift CI jobs.
  - The issues created are provided with any logs or junit files found in a failed step.
  - The issues can be created in any Jira instance or project (provided the proper credentials are supplied).
  - If multiple issues are created for a run, the issues will all be related to each other to help with issue.
  - The issues created have a "classification" section that is defined by the user in their firewatch config.
    - This can be used as a "best-guess" for what may have gone wrong during the job's run.
  - Firewatch will search for any past issues created by a specific step that has failed in the same way (pod failure or test failure) and list the 10 most recent ones.
    - This is meant to help the engineer working on the bug to find a solution.
  - Firewatch searches for duplicate issues and makes a comment on the issues rather than filing a second issue.
    - This is done using the labels on issues created by firewatch. These labels should consist of the failure type, failed step, and the job name.
    - If the new failures matches the failure type, failed step, and job name; firewatch will make a comment notifying the user that this failure likely happened again.
  - If no failures are found, firewatch will search for any open issues on the Jira server provided and add a comment to the issue mentioning that the job has passed since that issue was filed.
    - This functionality also uses the labels on issues created by firewatch.
    - **Note:** If you get a notification on an issue, but would like to continue working on the issue without getting notifications, add the `ignore-passing-notification` label to the issue.
  - If firewatch config contains job success reporting, a jira will be created (with status `closed`) reporting the job success

## Getting Started

### Usage in OpenShift CI

Reporting issues using this tool in OpenShift CI is very simple, you can do one of the following:

- Add the [`firewatch-report-issues` ref](https://github.com/openshift/release/tree/master/ci-operator/step-registry/firewatch/report-issues) to the `post` steps of a test. This job should be last, if that is not possible, make sure it is at least following any step that you'd like an issue generated for.
- Use a workflow with the [`firewatch-report-issues` ref](https://github.com/openshift/release/tree/master/ci-operator/step-registry/firewatch/report-issues) already in the `post` steps. For example, see the [`firewatch-ipi-aws` workflow](https://github.com/openshift/release/tree/master/ci-operator/step-registry/firewatch/ipi/aws).

Remember, when you are using the `firewatch-report-issues` ref, some variables need to be defined in your configuration file:

- `FIREWATCH_CONFIG` [REQUIRED]
  - This value should be a list of rules you have defined for firewatch to report on.

  > **IMPORTANT:**
  >
  > For more information how to define these rules, please see the [configuration guide](docs/configuration_guide.md).

  - Example:

      ```yaml
      FIREWATCH_CONFIG: |
          [
              {"step": "exact-step-name", "failure_type": "pod_failure", "classification": "Infrastructure", "jira_project": "PROJECT", "jira_component": ["some-component"], "jira_assignee": "some-user@redhat.com"},
              {"step": "*partial-name*", "failure_type": "all", "classification":  "Misc.", "jira_project": "OTHER", "jira_component": ["component-1", "component-2"], "jira_priority": "major", "group": {"name": "some-group", "priority": 1}},
              {"step": "*ends-with-this", "failure_type": "test_failure", "classification": "Test failures", "jira_project": "TEST", "jira_epic": "EPIC-123", "jira_additional_labels": ["test-label-1", "test-label-2"], "group": {"name": "some-group", "priority": 2}},
              {"step": "*ignore*", "failure_type": "test_failure", "classification": "NONE", "jira_project": "NONE", "ignore": "true"},
              {"step": "affects-version", "failure_type": "all", "classification": "Affects Version", "jira_project": "TEST", "jira_epic": "EPIC-123", "jira_affects_version": "4.14"},
              {"job_success": true, "jira_project": "TEST", "jira_epic": "EPIC-123"}
          ]
      ```

- `FIREWATCH_JIRA_SERVER`
  - The Jira server to report to.
  - DEFAULT: `https://issues.stage.redhat.com`
- `FIREWATCH_JIRA_API_TOKEN_PATH`
  - The path to the file holding the Jira API token.
  - DEFAULT: `/tmp/secrets/jira/access_token`.
- `FIREWATCH_FAIL_WITH_TEST_FAILURES`
  - A variable that will determine if the `firewatch-report-issues` step will fail with a non-zero exit code if a test failure is found in a JUnit file.
  - DEFAULT: `"false"`
  - BEHAVIOR:
    - `"false"`: The `firewatch-report-issues` step will not fail with a non-zero exit code when test failures are found.
    - `"true"`: The `firewatch-report-issues` step will fail with a non-zero exit code when test failures are found.

### Local Usage

If you'd like to run firewatch locally, use the following instructions:

#### Docker (recommended)

1. Ensure you have [Docker installed](https://www.docker.com/get-started/) on your system.
2. Clone the repository: `git clone https://github.com/CSPI-QE/firewatch.git`.
3. Navigate to the project root in your terminal: `cd firewatch`.
4. Run the following to build and run a Docker container with firewatch installed: `make build-run`.
5. Use the `firewatch` command to execute the tool. See the [CLI usage guide](docs/cli_usage_guide.md) for instructions on using the tool.

#### Local Machine (using venv)

1. Clone the repository: `git clone https://github.com/CSPI-QE/firewatch.git`
2. Navigate to the project root: `cd firewatch`
3. Install the necessary dependencies: `make dev-environment`
4. Use the `firewatch` command to execute the tool. See the [CLI usage guide](docs/cli_usage_guide.md) for instructions on using the tool.

## Contributing

We welcome contributions to firewatch! If you'd like to contribute, please review our [Contribution Guidelines](docs/contribution_guide.md) for more information on how to get started.

## License

firewatch is released under the [GNU Public License](LICENSE).

## Contact

If you have any questions, suggestions, or feedback, feel free to reach out to us:

- Project Repository: [CSPI-QE/firewatch](https://github.com/CSPI-QE/firewatch)
- Issue Tracker: [CSPI-QE/firewatch Issues](https://github.com/CSPI-QE/firewatch/issues)
- Slack: [#ocp-ci-firewatch-tool](https://redhat-internal.slack.com/archives/C062WMK4MCM)

We appreciate your interest in firewatch!
