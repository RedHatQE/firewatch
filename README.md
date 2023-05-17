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

If you'd like to run firewatch locally, use the following instructions:

### Docker (recommended)

1. Ensure you have [Docker installed](https://www.docker.com/get-started/) on your system.
2. Clone the repository: `git clone https://github.com/CSPI-QE/firewatch.git`
3. Navigate to the project root in your terminal: `cd firewatch`
4. Run the following to build and run a Docker container with firewatch installed: `make build-run`

### Local Machine (using venv)

1. Clone the repository: `git clone https://github.com/CSPI-QE/firewatch.git`
2. Navigate to the project root: `cd firewatch`
3. Install the necessary dependencies: `make dev-environment`


## Contributing

We welcome contributions to firewatch! If you'd like to contribute, please review our [Contribution Guidelines](docs/CONTRIBUTING.md) for more information on how to get started.

## License

firewatch is released under the [MIT License](LICENSE).

## Contact

If you have any questions, suggestions, or feedback, feel free to reach out to us:

- Project Repository: [https://github.com/CSPI-QE/firewatch](https://github.com/CSPI-QE/firewatch)
- Issue Tracker: [https://github.com/CSPI-QE/firewatch/issues](https://github.com/CSPI-QE/firewatch/issues)

We appreciate your interest in firewatch!
