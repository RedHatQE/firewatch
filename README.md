# firewatch

The firewatch project is in its infancy and currently has limited functionality. Ultimately, we'd like this tool to be a way to manage, track, and react to job failures in OpenShift CI.

**What may be added in future?**

- Automatic re-tries for user-defined failures in an OpenShift CI job.

## Features

- Automatically creates Jira issues for failed OpenShift CI jobs.
  - The issues created are provided with any logs or junit files found in a failed step.
  - The issues can be created in any Jira instance or project (provided the proper credentials are supplied).
  - If multiple issues are created for a run, the issues will all be related to each other to help with issue.
  - The issues created have a "classification" section that is defined by the user in their firewatch config.
    - This can be used as a "best-guess" for what may have gone wrong during the job's run.

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
            {"step": "exact-step-name", "failure_type": "pod_failure", "classification": "Infrastructure", "jira_project": "PROJECT", "jira_component": "some-component", "jira_assignee": "some-user@redhat.com"},
            {"step": "*partial-name*", "failure_type": "all", "classification":  "Misc.", "jira_project": "OTHER", "jira_component": ["component-1", "component-2"], "jira_priority": "major"},
            {"step": "*ends-with-this", "failure_type": "test_failure", "classification": "Test failures", "jira_project": "TEST", "jira_epic": "EPIC-123", "jira_additional_labels": ["test-label-1", "test-label-2"]},
            {"step": "*ignore*", "failure_type": "test_failure", "classification": "NONE", "jira_project": "NONE", "ignore": "true"},
            {"step": "affects-version", "failure_type": "all", "classification": "Affects Version", "jira_project": "TEST", "jira_epic": "EPIC-123", "jira_affects_version": "4.14"}
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

We welcome contributions to firewatch! If you'd like to contribute, please review our [Contribution Guidelines](docs/CONTRIBUTING.md) for more information on how to get started.

## License

firewatch is released under the [GNU Public License](LICENSE).

## Contact

If you have any questions, suggestions, or feedback, feel free to reach out to us:

- Project Repository: [https://github.com/CSPI-QE/firewatch](https://github.com/CSPI-QE/firewatch)
- Issue Tracker: [https://github.com/CSPI-QE/firewatch/issues](https://github.com/CSPI-QE/firewatch/issues)

We appreciate your interest in firewatch!
