# Copyright (C) 2023 Red Hat, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import os
from pathlib import Path

import pytest
import simple_logger.logger

from cli.gitleaks import DEFAULT_SERVER_URL
from cli.gitleaks import GitleaksConfig
from cli.report import Report

_logger = simple_logger.logger.get_logger(__name__)


@pytest.fixture
def gitleaks_config(init_gitleaks_config):
    yield init_gitleaks_config()


@pytest.fixture
def init_gitleaks_config(
    tmp_path,
    common_osci_env,
    patterns_server_token_path,
    job_dir,
):
    def _init(
        _job_dir=job_dir,
        _keep_job_dir=True,
        _token_path=patterns_server_token_path.as_posix(),
        _server_url=DEFAULT_SERVER_URL,
        _output_file="gitleaks-report.json",
    ):
        return GitleaksConfig(
            _server_url=_server_url,
            _token_path=_token_path,
            _output_file=_output_file,
            _job_dir=_job_dir,
            _keep_job_dir=_keep_job_dir,
            _keep_patterns_file=True,
        )

    yield _init


@pytest.fixture
def common_osci_env(build_id_from_env, artifact_dir, patterns_server_token_path):
    ...


@pytest.fixture
def job_dir(tmp_path, build_id_from_env):
    tmp_job_dir = tmp_path / build_id_from_env
    tmp_job_dir.parent.mkdir(exist_ok=True, parents=True)
    injected_leak_logs_path = tmp_job_dir / "logs/fake-step/fake-build-log.txt"
    injected_leak_junit_path = tmp_job_dir / "artifacts/fake-step/fake-build-log.txt"
    injected_leak_logs_path.parent.mkdir(parents=True, exist_ok=True)
    injected_leak_junit_path.parent.mkdir(parents=True, exist_ok=True)
    fake_secret = "aws_se" + 'cret="AKIAI' + 'MNOJVGFDXXXE4OA"'
    injected_leak_logs_path.write_text(fake_secret)
    injected_leak_junit_path.write_text(fake_secret)
    yield tmp_job_dir


@pytest.fixture
def build_id_from_env(monkeypatch):
    key = "BUILD_ID"
    val = "123456789"
    monkeypatch.setenv(key, val)
    yield os.getenv(key)


@pytest.fixture
def artifact_dir(artifact_dir_from_env):
    path = Path(artifact_dir_from_env)
    path.mkdir(parents=True, exist_ok=True)
    yield artifact_dir


@pytest.fixture
def artifact_dir_from_env(monkeypatch, tmp_path):
    key = "ARTIFACT_DIR"
    val = (tmp_path / "artifacts").as_posix()
    monkeypatch.setenv(key, val)
    yield os.getenv(key)


@pytest.fixture
def patterns_server_token_path(tmp_path, patterns_server_token_from_env):
    path = tmp_path / "secret/rh-patterns-server"
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text(patterns_server_token_from_env)
    yield path


@pytest.fixture
def patterns_server_token_from_env():
    var = os.getenv("PATTERNS_SERVER_TOKEN")
    if not var:
        pytest.fail(
            f"PATTERNS_SERVER_TOKEN was not found in the environment!",
        )
    yield var


@pytest.fixture
def report_with_gitleaks_no_leaks(monkeypatch, firewatch_config, job, tmp_path):
    def _job_dir(*args, **kwargs):
        _logger.info("Patching GitleaksConfig.job_dir")
        new_job_dir = tmp_path / "123456789"
        job_artifact_path = new_job_dir / "log/fake-step/build.log"
        job_artifact_path.parent.mkdir(parents=True, exist_ok=True)
        job_artifact_path.write_text("No leaks should be detected here.")
        return new_job_dir

    monkeypatch.setattr(GitleaksConfig, "_job_dir", _job_dir)
    yield Report(firewatch_config=firewatch_config, job=job, gitleaks=True)


@pytest.fixture(autouse=True)
def gitleaks_caplogs(caplog):
    gitleaks_logger = simple_logger.logger.get_logger("cli.gitleaks.gitleaks")
    gitleaks_logger.addHandler(caplog.handler)
    yield caplog
