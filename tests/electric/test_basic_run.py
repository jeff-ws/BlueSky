"""
Created as part of the C-NEMS Project

Written by:  J. F. Hyink
Contact:  jeff@westernspark.us
Created on:  6/15/26

A temporary (?) test to lock down the current outputs of a basic no-frills test run

"""

from pathlib import Path

import pytest
from pyomo.common.numeric_types import value

from definitions import PROJECT_ROOT
from src.common import config_setup
from src.models.electricity.elec_config import ElecConfig
from src.models.electricity.runner import run_elec_model

configs = [
    ('basic_elec_config.toml', 3452103301.9, 17886, 19440),
    ('exchange_elec_config.toml', 2278237043.0, 21342, 23088),
    ('expansion_no_learning_elec_config.toml', 3455793875.5, 18060, 19566),
]


@pytest.mark.parametrize(
    'config_file,expected_total_cost,expected_nvariables,expected_nconstraints',
    configs,
    ids=['Basic No-Frills', 'Exchange Enabled', 'Expansion (no learning)'],
)
def test_basic_run(config_file, expected_total_cost, expected_nvariables, expected_nconstraints):
    """
    Perform a couple of basic runs (with some features in isolation) and compare results to captured values

    dev notes:
    1.  basic config file turns OFF many features that may need separate verification
    2.  the values captured here for test were generated from run of legacy code and are *assumed*
        good for this test and dataset
    """
    config_path = Path(PROJECT_ROOT, 'tests/electric/meta_config.toml')
    settings = config_setup.Config_settings(config_path, test=True)

    # introduce the new ElecConfig
    elec_config_path = Path(PROJECT_ROOT, 'tests/electric', config_file)
    elec_config = ElecConfig.from_toml(elec_config_path)

    elec_model = run_elec_model(settings, elec_config, solve=True)

    assert value(elec_model.total_cost) == pytest.approx(expected_total_cost), (
        f'found {value(elec_model.total_cost)} total cost'
    )
    assert elec_model.nvariables() == expected_nvariables, (
        f'found {elec_model.nvariables()} variables'
    )
    assert elec_model.nconstraints() == expected_nconstraints, (
        f'found {elec_model.nconstraints()} constraints'
    )
