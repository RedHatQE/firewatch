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
from typing import Callable

from cli.gitleaks import GitleaksConfig


def test_init_gitleaks_config_returns_callable_gitleaks_config_init_fixture(
    init_gitleaks_config,
):
    assert isinstance(init_gitleaks_config, Callable)
    config = init_gitleaks_config()
    assert isinstance(config, GitleaksConfig)


def test_get_instantiated_gitleaks_config_from_fixture(gitleaks_config):
    assert isinstance(gitleaks_config, GitleaksConfig)
