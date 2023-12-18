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
