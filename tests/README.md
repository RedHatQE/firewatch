# Running Tests for Firewatch

This directory contains tests for the Firewatch project. The tests are designed to ensure the correctness and reliability of the codebase.

## Structure

The tests are organized into subdirectories that mirror the structure of the source code. Each test file corresponds to a specific module or class in the source code.

## Running the Unit Tests

You can use tox from command line to execute the unit tests. The tox.ini file defines the tox config for automatically running the tests. Tox installs the project dependencies and runs the tests using pytest command.
To invoke the pytest test execution command using tox, simply run the following command at project root directory:

```sh
tox
```

This will run all the tests under the directory tests/unittests with specified coverage.

To run all tests in a single file/module, you can execute pytest command with necessary options, for example:

```sh
pytest -c ./tests/unittests/pytest.ini --verbose ./tests/unittests/objects/job/test_firewatch_objects_job_check_is_rehearsal.py
```

To run a single unit test from a module, you can specify the function name like below:

```sh
pytest --verbose ./tests/unittests/objects/job/test_firewatch_objects_job_check_is_rehearsal.py::test_rehearsal_job_true
```

Alternatively you can use the python `unittest` framework. The following command will discover and run all the tests in the `tests/unittests` directory:

```sh
python -m unittest discover -s tests/unittests
```

You can run tests in a specific test file using option like below:

```sh
python -m unittest tests.unittests.objects.job.test_firewatch_objects_job_check_is_rehearsal
```

## Running the E2E Tests

To run the E2E tests, you can also use the `pytest` framework. The following command will discover and run all the tests in the `tests/e2e` directory. This directory contains end-to-end (E2E) tests for the Firewatch project. The tests are designed to ensure that the entire system works as expected, from start to finish.

```sh
pytest tests/e2e
```

## Mocking

The tests make extensive use of the `pytest` and `unittest.mock` libraries to mock external dependencies such as the JIRA API and the file system. This allows the tests to run in isolation and ensures that they are not affected by external factors.

## Adding New Tests

To add new tests, create a new test file in the appropriate subdirectory and follow the existing structure. Use the `pytest` framework and the `unittest.mock` library as needed.
