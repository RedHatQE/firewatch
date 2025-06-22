import tempfile
import yaml
from dynaconf import Dynaconf
from cerberus import Validator
from pathlib import Path
from pathlib import PurePath
from src.project.utils import get_project_config_data
from src.project.constants import SCHEMA, PROJECT_TEMPLATE_PATH
from typing import Optional


def validate_settings(settings):
    v = Validator(SCHEMA)
    flat_dict = settings.as_dict()  # Convert Dynaconf to plain dict
    if not v.validate(flat_dict):
        raise ValueError(f"Config validation error: {v.errors}")


def load_settings_from_dict(
    config_path: Optional[str] = None, template_file=PROJECT_TEMPLATE_PATH, env_prefix="FIREWATCH"
):
    if config_path:
        config_dict = get_project_config_data(project_file_path=config_path)
        current_directory = Path().resolve()
        settings_file = PurePath(current_directory, template_file)

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as tmpfile:
            yaml.dump(config_dict, tmpfile)
            tmpfile_path = tmpfile.name

        return Dynaconf(
            settings_files=[settings_file, tmpfile_path],
            lowercase_read=True,
            environments=False,
            envvar_prefix=env_prefix,
        )
