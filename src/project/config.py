import tempfile
import yaml
from dynaconf import Dynaconf
from pathlib import Path
from pathlib import PurePath
from src.project.utils import get_project_config_data
from src.project.constants import PROJECT_DATA_SCHEMA, PROJECT_TEMPLATE_PATH
from typing import Optional


def validate_settings(settings: dict, schema=PROJECT_DATA_SCHEMA):
    errors = []
    for key, value in settings.items():
        if not value:
            # Missing value
            continue
        schema_key = schema.get(key.lower())
        if not schema_key:
            # Redundant/extra var. Not applied on Firewatch. will not check
            continue
        expected_type = schema_key.get("type")
        if expected_type:
            if not isinstance(value, expected_type):
                errors.append(
                    f"Key '{key}' has invalid type: expected {expected_type.__name__}, "
                    f"got {type(value).__name__} (value={value})"
                )
    if errors:
        raise ValueError("Config validation failed:\n" + "\n".join(errors))


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
