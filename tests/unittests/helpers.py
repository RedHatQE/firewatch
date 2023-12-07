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
import os
import shutil
from pathlib import Path


def _create_successful_step_junit(
    junit_dir: str,
    step_name: str = "successful-step",
) -> str:
    current_dir = str(os.path.dirname(__file__))
    success_path = f"{junit_dir}/{step_name}"
    if not os.path.exists(success_path):
        os.mkdir(success_path)
    shutil.copy(f"{current_dir}/resources/junit_success.xml", success_path)

    return success_path


def _create_failed_step_junit(junit_dir: str, step_name: str = "failed-step") -> str:
    current_dir = str(os.path.dirname(__file__))
    failed_path = f"{junit_dir}/{step_name}"
    if not os.path.exists(failed_path):
        os.mkdir(failed_path)
    shutil.copy(f"{current_dir}/resources/junit_fail.xml", failed_path)

    return failed_path


def _create_successful_step_pod(
    logs_dir: str,
    step_name: str = "successful-step",
) -> str:
    current_dir = str(os.path.dirname(__file__))
    success_path = f"{logs_dir}/{step_name}"
    if not os.path.exists(success_path):
        os.mkdir(success_path)
    shutil.copy(
        f"{current_dir}/resources/pod_success.json",
        f"{success_path}/finished.json",
    )

    return success_path


def _create_failed_step_pod(logs_dir: str, step_name: str = "failed-step") -> str:
    current_dir = str(os.path.dirname(__file__))
    failed_path = f"{logs_dir}/{step_name}"
    if not os.path.exists(failed_path):
        os.mkdir(failed_path)
    shutil.copy(
        f"{current_dir}/resources/pod_fail.json",
        f"{failed_path}/finished.json",
    )

    return failed_path


def _get_tmp_logs_dir(tmp_path: str) -> str:
    logs_dir = f"{tmp_path}/logs"
    if not os.path.exists(logs_dir):
        os.mkdir(logs_dir)
    return logs_dir


def _get_tmp_junit_dir(tmp_path: str) -> str:
    junit_dir = f"{tmp_path}/artifacts"
    if not os.path.exists(junit_dir):
        os.mkdir(junit_dir)
    return junit_dir
