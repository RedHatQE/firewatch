# Contributing to firewatch

Thank you for your interest in contributing to the firewatch project! We welcome any contributions that help improve the project and make it more robust. This document outlines the guidelines for contributing to the project. Please take a moment to review these guidelines before making your contributions.

## Table of Contents

- [Types of Contributions](#types-of-contributions)
- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Submitting Contributions](#submitting-contributions)

## Types of Contributions

We appreciate any form of contribution, including but not limited to:

- Bug fixes
- New features
- Documentation improvements
- Code optimizations
- Test coverage improvements

## Code of Conduct

We strive to maintain a friendly and inclusive community. We have not yet established a formal code of conduct, but we expect all contributors to adhere to the principles of respect, open-mindedness, and professionalism. Please be kind and considerate when interacting with others.

## Development Setup

1. Fork the repository on GitHub.
2. Clone your forked repository to your local machine.
3. Navigate to the project root: `cd firewatch`
4. Install the necessary dependencies: `make dev-environment`
5. Run pre-commit hooks to ensure code quality: `make pre-commit`
6. Execute tests to ensure everything is working correctly: `tox` or `make test`

## Testing Changes

### Container

   1. Find a failed prow job you would like to test against.
      - **Example**: [periodic-ci-openshift-pipelines-release-tests-release-v1.11-openshift-pipelines-ocp4.14-lp-interop-openshift-pipelines-interop-aws #1696039978221441024](https://prow.ci.openshift.org/view/gs/test-platform-results/logs/periodic-ci-openshift-pipelines-release-tests-release-v1.11-openshift-pipelines-ocp4.14-lp-interop-openshift-pipelines-interop-aws/1696039978221441024)
   2. Fill out `firewatch/development/env.list`
      - Use the ["Defining Environment Variables"](#defining-environment-variables) section to help
   3. From the root of this repository, run `make container-build-test` to execute `firewatch report` using the values provided above.
      - You can also run `make container-build-run` if you would like a bash terminal for the new build.

### Local Machine

1. Create your development environment if you haven't already (execute from the root of the firewatch repository):
    - `$ make dev-environment`
2. Find a failed prow job you would like to test against.
      - **Example**: [periodic-ci-openshift-pipelines-release-tests-release-v1.11-openshift-pipelines-ocp4.14-lp-interop-openshift-pipelines-interop-aws #1696039978221441024](https://prow.ci.openshift.org/view/gs/test-platform-results/logs/periodic-ci-openshift-pipelines-release-tests-release-v1.11-openshift-pipelines-ocp4.14-lp-interop-openshift-pipelines-interop-aws/1696039978221441024)
2. Export the required environment varaibles:
   - Use the ["Defining Environment Variables"](#defining-environment-variables) section to help

   ```bash
    export JIRA_TOKEN=""
    export JIRA_SERVER=""
    export BUILD_ID=""
    export JOB_NAME_SAFE=""
    export JOB_NAME=""
    export FIREWATCH_CONFIG=""
    export FIREWATCH_DEFAULT_JIRA_PROJECT=""
    ```

3. Create the Jira config file (execute from the root of the firewatch repository)
   - `$ echo $JIRA_TOKEN > /tmp/token && poetry run firewatch jira-config-gen --token-path /tmp/token --server-url $JIRA_SERVER --template-path $(pwd)/cli/templates/jira.config.j2`
4. Execute firewatch (execute from the root of the firewatch repository)
   - `$ poetry run firewatch report`

### Defining Environment Variables

- `JIRA_TOKEN`: The token needed to log in to the Jira service account that firewatch will use.
- `JIRA_SERVER`: URL to Jira server you would like to test against (should be `https://issues.stage.redhat.com`)
- `BUILD_ID`: Build ID from failed job you are testing with (`1696039978221441024` if using job from the example in step 1)
- `JOB_NAME_SAFE`: Safe job name from the prow job you are testing with (`openshift-pipelines-interop-aws` if using the job from the example in step 1)
- `JOB_NAME`: Full prow job name that you are testing with (`periodic-ci-openshift-pipelines-release-tests-release-v1.11-openshift-pipelines-ocp4.14-lp-interop-openshift-pipelines-interop-aws` if using the job from the example in step 1)
- `FIREWATCH_CONFIG`: Config you would like to test with. Use the [configuration guide](configuration_guide.md) for help.
- `FIREWATCH_DEFAULT_JIRA_PROJECT`: Default project you'd like to report failures to if a rule doesn't match a failure.

## Submitting Contributions

Contributions to firewatch are made through pull requests. To submit your contributions, please follow these steps:

1. Fork the repository on GitHub.
2. Clone your forked repository to your local machine.
3. Create a new branch for your feature or bug fix: `git checkout -b my-feature`
4. Make your desired changes and ensure they follow the linting rules enforced by the pre-commit hooks.
5. Write unit tests for any new code you are adding.
6. Update the documentation if necessary.
7. Commit your changes with descriptive commit messages.
8. Push your branch to your forked repository on GitHub: `git push origin my-feature`
9. Open a pull request from your branch to the `main` branch of the main repository.
10. Provide a clear and concise description of your changes in the pull request, including any relevant details or context.

Once your pull request is submitted, our team will review it as soon as possible. We may provide feedback or ask for additional changes before merging your contribution.

Thank you for contributing to firewatch! Your help is greatly appreciated.
