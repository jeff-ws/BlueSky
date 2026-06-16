"""
Created as part of C-NEMS Project

Written by:  J. F. Hyink
Contact:  jeff@westernspark.us
Created on:  6/13/26

Module to read structured .csv files and prepare dictionary-based data for model parameter
initialization

"""

from collections.abc import Iterable, Sequence
from csv import DictReader
from dataclasses import dataclass
from pathlib import Path

from definitions import PROJECT_ROOT

param_sources = {
    #             Filename,     columns to index,                   value
    'cap_cost': ('CapCost.csv', ('region', 'tech', 'year', 'step'), 'cost'),
}
protperty_sources = {
    #             Filename,        expected header: columns to properties [first=basis]
    'tech_data': (
        'tech_data.csv',
        'tech,T_conv,T_re,T_hydro,T_stor,T_vre,T_wind,T_solar,T_h2,T_disp,T_gen',
    ),
    'region_data': ('region_data.csv', 'region,domestic,international'),
}


@dataclass
class FilterPackage:
    """Container to hold the values to use for filtering and the column names they apply to
    Example:
        region_filter = {'south', 'west'}
        region_cols = ['region', 'region_destination']
        year_filter = {'2025', '2042'}
        year_col = 'year'
    """

    region_filter: set[str] | None = None
    region_cols: Iterable[str] | None = None
    year_filter: set[str] | None = None
    year_col: str | None = None


def read_parameter_csv(
    file_path: Path,
    index_cols: Sequence[str] | None,
    value_col: str,
    filter_package: FilterPackage | None = None,
    year_col: int = -1,
) -> dict[tuple[str, ...], float]:
    """
    Reads a CSV file and processes its content into a dictionary mapping index tuples
    to float values while applying optional region and year filtering.
    """
    with open(file_path, 'r') as f:
        res = {}
        reader = DictReader(f)
        for line in reader:
            tokens = line.strip().split(',')
            idx_portion = tuple(tokens[:-1])
            # filter while reading
            if region_filter:
                regions = set(tokens[c] for c in region_cols)
                if not regions.issubset(region_filter):
                    continue
            if year_filter:
                if tokens[year_col] not in year_filter:
                    continue
            value = float(tokens[-1])
            res[idx_portion] = value
    return res


def read_property_csv(file_path: Path, expected_header: str = None) -> dict[str, list[str]]:
    """read in the technology csv file and sort the techs into a master set and subsets based on
    column headers"""

    with open(file_path, 'r') as f:
        header = f.readline().strip()
        if expected_header and header != expected_header:
            raise ValueError(
                f'Expected header in file {file_path}: \n{expected_header}\ngot: \n{header}'
            )
        header_index = {idx: label for idx, label in enumerate(expected_header.split(','))}
        # make set of dictionaries to catch the "True" vals
        res = {label: [] for label in header_index.values()}
        for line in f:
            tokens = line.strip().split(',')
            res[header_index[0]].append(tokens[0])
            for idx, token in enumerate(tokens[1:], start=1):
                if token.lower() == 'true':
                    res[header_index[idx]].append(tokens[0])
    return res


def load_param_data(
    input_dir: Path, region_filter: set[str] | None = None, year_filter: set[str] | None = None
) -> dict[str, dict[tuple[str, ...], float]]:
    return dict(
        (k, read_parameter_csv(input_dir / v[0], region_filter, year_filter, v[1], v[2]))
        for k, v in param_sources.items()
    )


def load_property_data(
    input_dir: Path, expected_header: str = None
) -> dict[str, dict[str, list[str]]]:
    return dict(
        (k, read_property_csv(input_dir / v[0], expected_header=v[1]))
        for k, v in protperty_sources.items()
    )


if __name__ == '__main__':
    regions = set(list('478'))
    years = {'2025', '2042'}
    source_dir = PROJECT_ROOT / 'input/electricity/cem_inputs'
    print(load_param_data(source_dir, regions, years))

    print(
        read_property_csv(
            PROJECT_ROOT / 'input/electricity/tech_data.csv',
            expected_header='tech,T_conv,T_re,T_hydro,T_stor,T_vre,T_wind,T_solar,T_h2,T_disp,T_gen',
        )
    )
    print(
        read_property_csv(
            PROJECT_ROOT / 'input/electricity/region_data.csv',
            expected_header='region,domestic,international',
        )
    )
