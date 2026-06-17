"""
Created as part of C-NEMS Project

Written by:  J. F. Hyink
Contact:  jeff@westernspark.us
Created on:  6/13/26

Module to read structured .csv files and prepare dictionary-based data for model parameter
initialization

"""

import logging
from collections.abc import Iterable, Sequence
from csv import DictReader
from dataclasses import dataclass
from pathlib import Path

from definitions import PROJECT_ROOT

logger = logging.getLogger(__name__)

# TODO:  There is some inconsistency in the column ordering here, but it is captured as-is for now
#        to align with the model.  This code will work fine if the columns are re-sequenced here and
#        it will render the index in the order given here
param_sources = {
    # key: (Filename, columns to index, value)
    'battery_efficiency': ('BatteryEfficiency.csv', ('tech',), 'BatteryEfficiency'),
    'cap_cost': ('CapCost.csv', ('region', 'tech', 'year', 'step'), 'CapCost'),
    'cap_cost_initial': ('CapCostInitial.csv', ('region', 'tech', 'step'), 'CapCostInitial'),
    'cap_factor_vre': ('CapFactorVRE.csv', ('tech', 'region', 'step', 'hour'), 'CapFactorVRE'),
    'fom_cost': ('FOMCost.csv', ('region', 'tech', 'step'), 'FOMCost'),
    'h2_price': ('H2Price.csv', ('region', 'season', 'tech', 'step', 'year'), 'H2Price'),
    'hours_to_buy': ('HourstoBuy.csv', ('tech',), 'HourstoBuy'),
    'hydro_cap_factor': ('HydroCapFactor.csv', ('region', 'season'), 'HydroCapFactor'),
    'learning_rate': ('LearningRate.csv', ('tech',), 'LearningRate'),
    'ramp_down_cost': ('RampDownCost.csv', ('tech',), 'RampDownCost'),
    'ramp_rate': ('RampRate.csv', ('tech',), 'RampRate'),
    'ramp_up_cost': ('RampUpCost.csv', ('tech',), 'RampUpCost'),
    'reg_reserves_cost': ('RegReservesCost.csv', ('tech',), 'RegReservesCost'),
    'reserve_margin': ('ReserveMargin.csv', ('region',), 'ReserveMargin'),
    'res_tech_upper_bound': ('ResTechUpperBound.csv', ('restype', 'tech'), 'ResTechUpperBound'),
    'supply_curve': ('SupplyCurve.csv', ('region', 'tech', 'step', 'year'), 'SupplyCurve'),
    'supply_curve_learning': ('SupplyCurveLearning.csv', ('tech',), 'SupplyCurveLearning'),
    'supply_price': (
        'SupplyPrice.csv',
        ('region', 'season', 'tech', 'step', 'year'),
        'SupplyPrice',
    ),
    'tran_cost': ('TranCost.csv', ('region', 'region1', 'year'), 'TranCost'),
    'tran_cost_int': ('TranCostInt.csv', ('region', 'region1', 'step', 'year'), 'TranCostInt'),
    'tran_limit': ('TranLimit.csv', ('region', 'region1', 'season', 'year'), 'TranLimit'),
    'tran_limit_cap_int': (
        'TranLimitCapInt.csv',
        ('region', 'region1', 'year', 'season'),
        'TranLimitCapInt',
    ),
    'tran_limit_gen_int': (
        'TranLimitGenInt.csv',
        ('region1', 'step', 'year', 'season'),
        'TranLimitGenInt',
    ),
}
protperty_sources = {
    # Filename, columns to property-ize, index/basis cols
    'tech_data': (
        'tech_data.csv',
        'tech,T_conv,T_re,T_hydro,T_stor,T_vre,T_wind,T_solar,T_h2,T_disp,T_gen'.split(','),
        ('tech',),
    ),
    'buildable_techs': ('build_data.csv', ['builds'], ('tech', 'step')),
    'retireable_techs': (
        'retire_data.csv',
        ['retires'],
        ('tech', 'step'),
    ),
    'region_data': ('region_data.csv', ['region', 'domestic', 'international'], ('region',)),
}

# columns we always want to convert to integer to enable arithmetic on them...
INTEGER_COLS = {'step', 'year', 'hour'}


@dataclass
class FilterPackage:
    """Container to hold the values to use for filtering and the column names they apply to
    Example:
        region_filter = {'south', 'west'}
        region_cols = ['region', 'region_destination']
        year_filter = {2025, 2042}
        year_col = 'year'

        would allow 'south' and 'west' columns 'region' and 'region_destination' and
        '2025' and '2042' in 'year'
    """

    region_filter: set[str] | None = None
    region_cols: Iterable[str] = ('region', 'region1', 'destination_region', 'source_region')
    year_filter: set[int] | None = None
    year_col: Iterable[str] = ('year',)


def read_parameter_csv(
    file_path: Path,
    index_cols: Sequence[str],
    value_col: str,
    filter_package: FilterPackage | None = None,
) -> dict[tuple[str, ...], float]:
    """
    Reads a CSV file and processes its content into a dictionary mapping index tuples
    to float values while applying optional region and year filtering.

    """
    with open(file_path, 'r') as f:
        res = {}
        reader = DictReader(f)
        flag_floats = False
        for row in reader:
            # convert integer columns to int
            for col in INTEGER_COLS:
                if col in row:
                    try:
                        row[col] = int(row[col])
                    except ValueError:
                        try:
                            row[col] = int(float(row[col]))
                            flag_floats = True
                        except ValueError:
                            logger.error(
                                'Unable to convert %s to int in file %s', row[col], file_path
                            )
                            raise (
                                ValueError(
                                    f'Unable to convert {row[col]} to int in file {file_path}'
                                )
                            )

            # apply filters, if any
            if filter_package:
                if filter_package.region_filter:
                    discovered_regions = set(row[col] for col in filter_package.region_cols)
                    if not discovered_regions.issubset(filter_package.region_filter):
                        continue
                if filter_package.year_filter:
                    discovered_years = set(row[col] for col in filter_package.year_col)
                    if not discovered_years.issubset(filter_package.year_filter):
                        continue

            # make an index tuple
            try:
                idx = tuple(row[col] for col in index_cols)
            except KeyError:
                logger.error('Expecting index columns %s in csv file: %s', index_cols, file_path)
                raise

            # capture the value
            try:
                value = float(row[value_col])
            except ValueError:
                logger.error(
                    'Expecting float value in column %s in csv file: %s', value_col, file_path
                )
                raise
            res[idx] = value
    if flag_floats:
        logger.warning('Converted floats to ints in %s', file_path)
    return res


def read_property_csv(
    file_path: Path, param_cols: Iterable[str], index_cols: Iterable[str]
) -> dict[str, list[str]]:
    """read csv file that has 'properties as columns' and some index columns and convert
    to dictionary of indices that satisfy each property (pivot)


    Assume the first column is the index/reference column and gather those entries in master set.
    For other columns, look for True/true and capture
    """

    with open(file_path, 'r') as f:
        reader = DictReader(f)
        flag_floats = False
        # make set of dictionaries to catch the "True" vals
        res = {label: [] for label in param_cols}
        for row in reader:
            # convert integer columns to int
            for col in INTEGER_COLS:
                if col in row:
                    try:
                        row[col] = int(row[col])
                    except ValueError:
                        try:
                            row[col] = int(float(row[col]))
                            flag_floats = True
                        except ValueError:
                            logger.error(
                                'Unable to convert %s to int in file %s', row[col], file_path
                            )
                            raise (
                                ValueError(
                                    f'Unable to convert {row[col]} to int in file {file_path}'
                                )
                            )

            # grab index
            try:
                idx = tuple(row[col] for col in index_cols)
                # de-tuple any singletons
                if len(idx) == 1:
                    idx = idx[0]
            except KeyError:
                logger.error('Expecting index columns %s in csv file: %s', index_cols, file_path)
                raise
            for col in param_cols:
                # look for "true" value in each property column, if found, add to that collection
                # also capture if the column name is in the index set to create master set(s)
                try:
                    token = row[col].lower()
                    if token == 'true' or col in index_cols:
                        res[col].append(idx)
                except KeyError:
                    logger.error('Expecting parameter column %s in csv file: %s', col, file_path)
                    raise
                except AttributeError:
                    logger.error(
                        'Problem converting / comparing value %s of type %s with string values in csv file: %s',
                        row[col],
                        type(row[col]),
                        file_path,
                    )
                    raise
    if flag_floats:
        logger.warning('Converted floats to ints in %s', file_path)
    return res


def load_param_data(
    input_dir: Path, region_filter: set[str] | None = None, year_filter: set[str] | None = None
) -> dict[str, dict[tuple[str, ...], float]]:
    empty_filter = FilterPackage()
    return dict(
        (k, read_parameter_csv(input_dir / file_path, index_cols, value_col, empty_filter))
        for k, (file_path, index_cols, value_col) in param_sources.items()
    )


def load_property_data(input_dir: Path) -> dict[str, dict[str, list[str]]]:
    return dict(
        (k, read_property_csv(input_dir / filename, prop_cols, idx_cols))
        for k, (filename, prop_cols, idx_cols) in protperty_sources.items()
    )


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
    logger.debug('Testing the load_param_data and load_property_data functions')
    regions = set(list('478'))
    years = {'2025', '2042'}
    source_dir = PROJECT_ROOT / 'input/electricity/cem_inputs'
    for k, v in load_param_data(source_dir, regions, years).items():
        print(k, len(v))
    source_dir = PROJECT_ROOT / 'input/electricity'
    print('\n*** property data ***\n')
    data = load_property_data(source_dir)
    for k, v in data.items():
        print(k)
        for k2, v2 in v.items():
            print('  ', k2, len(v2))
