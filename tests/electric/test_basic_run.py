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
from src.models.electricity.scripts.runner import run_elec_model


def test_basic_run():
    """
    Perform a basic run of the electricity model and compare key values

    dev notes:
    1.  this config file turns OFF many features that may need separate verification
    2.  the values captured here for test were generated from run of legacy code and are *assumed*
        good for this test and dataset
    """
    config_path = Path(PROJECT_ROOT, 'tests/electric/basic_test_config.toml')
    settings = config_setup.Config_settings(config_path, test=True)

    elec_model = run_elec_model(settings, solve=True)

    assert value(elec_model.total_cost) == pytest.approx(3452103301.9), (
        f'found {value(elec_model.total_cost)} total cost'
    )
    assert elec_model.nvariables() == 17886, f'found {elec_model.nvariables()} variables'
    assert elec_model.nconstraints() == 19440, f'found {elec_model.nconstraints()} constraints'
