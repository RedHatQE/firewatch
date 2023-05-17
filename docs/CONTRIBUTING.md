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

To set up your development environment for firewatch, please follow these steps:

1. Fork the repository on GitHub.
2. Clone your forked repository to your local machine.
3. Navigate to the project root: `cd firewatch`
4. Install the necessary dependencies: `make dev-environment`
5. Run pre-commit hooks to ensure code quality: `make pre-commit`
6. Execute tests to ensure everything is working correctly: `tox` or `make test`

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
