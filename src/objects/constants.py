#
# Copyright (C) 2024 Red Hat, Inc.
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

# Default URL for the jira transition map if none is provided
DEFAULT_TRANSITION_MAP_URL = "https://raw.githubusercontent.com/CSPI-QE/cspi-utils/main/firewatch-base-configs/project_transition_map.json"
# Hardcoded default transition if map loading fails or DEFAULT is missing
FALLBACK_DEFAULT_TRANSITION = "CLOSED"
