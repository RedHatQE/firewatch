#
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
import pytest

from cli.gitleaks.constants import PATTERNS_SERVER_URL_VAR
from cli.gitleaks.gitleaks import GitleaksConfig


def test_init_minimal_gitleaks_config_without_warnings_or_errors(
    patterns_server_token_path,
    build_id_from_env,
    artifact_dir,
    gitleaks_caplogs,
    tmp_path,
):
    GitleaksConfig(
        _token_path=patterns_server_token_path,
        _output_file="",
        _job_dir=tmp_path,
    )
    for text in gitleaks_caplogs.text.splitlines():
        if "Last log repeated" not in text:
            assert "WARN" not in text
            assert "ERR" not in text


def test_missing_artifact_dir_env_var_raises_environment_error(
    monkeypatch,
    init_gitleaks_config,
):
    monkeypatch.setenv("ARTIFACT_DIR", "")
    with pytest.raises(EnvironmentError):
        init_gitleaks_config()


def test_missing_build_id_env_var_raises_environment_error(
    monkeypatch,
    init_gitleaks_config,
):
    monkeypatch.setenv("BUILD_ID", "")
    with pytest.raises(EnvironmentError):
        init_gitleaks_config()


def test_missing_artifact_dir_raises_environment_error(
    monkeypatch,
    tmp_path,
    init_gitleaks_config,
):
    monkeypatch.setenv("ARTIFACT_DIR", tmp_path.joinpath("_missing").as_posix())
    with pytest.raises(EnvironmentError):
        init_gitleaks_config()


def test_missing_job_dir_raises_environment_error(
    tmp_path,
    init_gitleaks_config,
    gitleaks_caplogs,
):
    with pytest.raises(EnvironmentError):
        init_gitleaks_config(_job_dir=tmp_path.joinpath("_missing"))

    exp = "the Firewatch report downloads directory was not found"
    assert exp in gitleaks_caplogs.text


def test_empty_job_dir_raises_environment_error(init_gitleaks_config, tmp_path):
    empty_job_dir = tmp_path / "_empty"
    empty_job_dir.mkdir(exist_ok=True, parents=True)
    with pytest.raises(EnvironmentError):
        init_gitleaks_config(_job_dir=empty_job_dir)


def test_missing_patterns_server_token_raises_environment_error(
    init_gitleaks_config,
    tmp_path,
):
    with pytest.raises(EnvironmentError):
        init_gitleaks_config(_token_path=tmp_path.joinpath("_nothing"))


def test_missing_patterns_server_url_raises_environment_error(
    monkeypatch,
    init_gitleaks_config,
    tmp_path,
):
    monkeypatch.setenv(PATTERNS_SERVER_URL_VAR, "")
    with pytest.raises(EnvironmentError):
        init_gitleaks_config()


def test_job_dir_is_removed_after_detect_scan(init_gitleaks_config, tmp_path):
    minimal_job_dir = tmp_path / "987654321"
    minimal_job_dir.mkdir(exist_ok=True, parents=True)
    minimal_job_dir.joinpath("artifact.txt").write_text("some text")
    config = init_gitleaks_config(
        _job_dir=minimal_job_dir,
        _keep_job_dir=False,
    )
    assert minimal_job_dir.is_dir()
    config.start_detect_scan()
    assert not minimal_job_dir.exists()


def test_fetch_patterns_from_patterns_server(gitleaks_config, tmp_path):
    patterns_path = tmp_path / "_tmp_patterns.toml"
    gitleaks_config._patterns_file_path = patterns_path
    assert not patterns_path.is_file()
    gitleaks_config._try_fetch_patterns_from_server()
    assert patterns_path.is_file()


def test_start_detect_scan_with_detections_creates_report(
    gitleaks_config: GitleaksConfig,
):
    assert not gitleaks_config.gitleaks_report_path.is_file()
    gitleaks_config.start_detect_scan()
    assert (
        gitleaks_config.gitleaks_report_path.is_file()
    ), "the gitleaks report file was not found"
    assert "aws_secret=REDACTED" in gitleaks_config.gitleaks_report_path.read_text()
