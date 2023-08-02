# Using the firewatch CLI

## Table of Contents

* [Using the firewatch CLI](#using-the-firewatch-cli)
  * [Installation](#installation)
    * [Docker (recommended)](#docker-recommended)
    * [Local Machine (using venv)](#local-machine-using-venv)
  * [Configuration](#configuration)
  * [Usage](#usage)
    * [`report`](#report)
    * [`jira_config_gen`](#jiraconfiggen)

## Installation

### Docker (recommended)

1. Ensure you have [Docker installed](https://www.docker.com/get-started/) on your system.
2. Clone the repository: `git clone https://github.com/CSPI-QE/firewatch.git`.
3. Navigate to the project root in your terminal: `cd firewatch`.
4. Run the following to build and run a Docker container with firewatch installed: `make build-run`.
5. Use the `firewatch` command to execute the tool. See the [CLI usage guide](docs/cli_usage_guide.md) for instructions on using the tool.

### Local Machine (using venv)

1. Clone the repository: `git clone https://github.com/CSPI-QE/firewatch.git`
2. Navigate to the project root: `cd firewatch`
3. Install the necessary dependencies: `make dev-environment`
4. Use the `firewatch` command to execute the tool. See the [CLI usage guide](docs/cli_usage_guide.md) for instructions on using the tool.

## Configuration

Please see the [configuration guide](configuration_guide.md) to help you build your configuration.

## Usage

### `report`

The `report` command is used to generate and file Jira issues for a failed OpenShift CI run using a [user-defined firewatch configuration](#configuration).
Many of the arguments for this command have set defaults or will use an environment variable.

**Pre-requisites:**

1. A Jira configuration file must exist. Use the `jira_config_gen` command to generate the configuration file.
2. A firewatch config must be defined. Use the [Configuration section above](#configuration) to generate your configuration.

**Arguments:**

```commandline
Usage: firewatch report [OPTIONS]

Options:
  --fail_with_test_failures     Firewatch will fail with a non-zero exit code
                                if a test failure is found.
  --jira_config_path TEXT       The path to the jira configuration file
                                [required]
  --firewatch_config_path TEXT  The path to the firewatch configuration file
  --gcs_bucket TEXT             The name of the GCS bucket that holds
                                OpenShift CI logs  [required]
  --build_id TEXT               The build ID that needs to be reported. The
                                value of $BUILD_ID
  --job_name_safe TEXT          The safe name of a test in a Prow job. The
                                value of $JOB_NAME_SAFE
  --job_name TEXT               The full name of a Prow job. The value of
                                $JOB_NAME
```

**Examples:**

```commandline
# Using all environment variables (Running in OpenShift CI uses this method)
$ export BUILD_ID="some_build_id"
$ export JOB_NAME_SAFE="some_safe_job_name"
$ export JOB_NAME="some_job_name"
$ export FIREWATCH_CONFIG="[{"step": "some-step-name","failure_type":"pod_failure", "classification": "some best guess classification", "jira_project": "PROJECT"}]"
$ firewatch report

# Using CLI arguments
$ firewatch report --build_id some_build_id --job_name_safe some_safe_job_name --job_name some_job_name --firewatch_config_path /some/path/to/firewatch_config.json

# Exit with a non-zero exit code if test failures are found in any JUnit file for a step
$ firewatch report --fail_with_test_failures

```

**Example of Jira Ticket Created:**

![Screenshot of an example Jira ticket](images/jira-ticket-example.png)

**How Are Duplicate Bugs Handled?**

This tool takes duplicate bugs into consideration. When a failure is identified, after the failure has been matched with its corresponding rule in the firewatch config, the firewatch tool will search Jira for any bugs that match the following rules to determine if it is a duplicate:

- Any OPEN issues that are in the same Jira project defined in the rule's `jira_project` key
- **AND** issues that have a label matching the step/pod name that failed
- **AND** issues that have a label matching the prow job name that failed
- **AND** issues that have a label matching the `failure_type` of the failure we are searching for

If any issues are found that match all the conditions above, we can be fairly confident that the failure may be a duplicate and the tool will make a comment on each of the matching issues that looks like this:

> A duplicate failure was identified in a recent run of the {job name} job:
>
> **Link:** {link to prow job run}
>
> **Build ID:** {failing build ID}
>
> **Classification:** {value of the "classification" key of the matching rule}
>
> **Pod Failed:** {name of step/pod that failed}
>
> Please see the link provided above to determine if this is the same issue. If it is not, please manually file a new bug for this issue.
>
> This comment was created using firewatch in OpenShift CI

**What about stale issues in Jira?**

This tool has functionality to find open Jira issues that were created for the passing job and created by firewatch. When no failures are found for a job, the firewatch tool will search Jira for any Jira issues that match the following rules:

- Any OPEN issues in the provided Jira server that:
- has a label matching the prow job name that passed
- **AND** has a label matching "firewatch" (this is to ensure the open issue is created by the firewatch tool)
- **AND** does NOT have a label matching "ignore-passing-notification" (this is to allow users to stop future notifications if they need to keep the issue open but don't want the notifications in the future)

If Any issues are found that match all the conditions above, we can be fairly confident that a "passing job" notification should be given in the form of a comment on the issue. The comment looks something like this:

>  **JOB RECENTLY PASSED**
>
> This job has been run successfully since this bug was filed. Please verify that this bug is still relevant and close it if needed.
>
> **Passing Run Link:** {link to prow job run}
>
> **Passing Run Build ID:** {passing build ID}
>
> *Please add the "ignore-passing-notification" tag to this bug to avoid future passing job notifications.*
>
> This comment was created using firewatch in OpenShift CI.

### `jira_config_gen`

The `jira_config_gen` command is used to generate the Jira configuration file used when firewatch interacts with a Jira server.

**Arguments:**

```commandline
Usage: firewatch jira_config_gen [OPTIONS]

Options:
  --output_file TEXT  Where the rendered config will be stored  [required]
  --token_path TEXT   Path to the Jira API token  [required]
  --server_url TEXT   Jira server URL, i.e "https://issues.stage.redhat.com"
                      [required]
  --help              Show this message and exit.
```

**Examples:**

```commandline
# Create a configuration file in the default location (/tmp/jira.config)
$ firewatch jira_config_gen --token_path {Path to file containing Jira API token} --server_url https://some.jira.server.com

# Create a configuration file in a different location (/some/path/jira.config)
$ firewatch jira_config_gen --token_path {Path to file containing Jira API token} --server_url https://some.jira.server.com --output_file /some/path
```
