import json
from pathlib import Path
from typing import List, Optional, Union, cast

import pandas as pd
from owid import catalog
from owid.datautils.common import ExceptionFromDocstring, warn_on_list_of_entities
from owid.datautils.dataframes import map_series
from owid.datautils.io.json import load_json


def _load_countries_regions() -> pd.DataFrame:
    countries_regions = catalog.find("regions", namespace="regions").load()
    return cast(pd.DataFrame, countries_regions)


def _load_income_groups() -> pd.DataFrame:
    income_groups = catalog.find(table="income_groups_latest").load()
    return cast(pd.DataFrame, income_groups)


class RegionNotFound(ExceptionFromDocstring):
    """Region was not found in countries-regions dataset."""


def list_countries_in_region(
    region: str,
    countries_regions: Optional[pd.DataFrame] = None,
    income_groups: Optional[pd.DataFrame] = None,
) -> List[str]:
    """List countries that are members of a region.

    Parameters
    ----------
    region : str
        Name of the region (e.g. Europe).
    countries_regions : pd.DataFrame or None
        Countries-regions dataset, or None to load it from the catalog.
    income_groups : pd.DataFrame or None
        Income-groups dataset, or None, to load it from the catalog.

    Returns
    -------
    members : list
        Names of countries that are members of the region.

    """
    if countries_regions is None:
        countries_regions = _load_countries_regions()

    # TODO: Remove lines related to income_groups once they are included in countries-regions dataset.
    if income_groups is None:
        income_groups = _load_income_groups().reset_index()
    income_groups_names = income_groups["classification"].dropna().unique().tolist()  # type: ignore

    # TODO: Once countries-regions has additional columns 'is_historic' and 'is_country', select only countries, and not
    #  historical regions.
    if region in countries_regions["name"].tolist():
        # Find codes of member countries in this region.
        member_codes_str = countries_regions[countries_regions["name"] == region][
            "members"
        ].item()
        if pd.isnull(member_codes_str):
            member_codes = []
        else:
            member_codes = json.loads(member_codes_str)
        # Get harmonized names of these countries.
        members = countries_regions.loc[member_codes][
            "name"
        ].tolist()  # type: List[str]
    elif region in income_groups_names:
        members = income_groups[income_groups["classification"] == region]["country"].unique().tolist()  # type: ignore
    else:
        raise RegionNotFound

    return members


def harmonize_countries(
    df: pd.DataFrame,
    countries_file: Union[Path, str],
    excluded_countries_file: Optional[Union[Path, str]] = None,
    country_col: str = "country",
    warn_on_missing_countries: bool = True,
    make_missing_countries_nan: bool = False,
    warn_on_unused_countries: bool = True,
    warn_on_unknown_excluded_countries: bool = True,
    show_full_warning: bool = True,
) -> pd.DataFrame:
    """Harmonize country names in dataframe, following the mapping given in a
    file.

    Countries in dataframe that are not in mapping will left unchanged (or
    converted to nan, if make_missing_countries_nan is True). If
    excluded_countries_file is given, countries in that list will be removed
    from the output data.

    Parameters
    ----------
    df : pd.DataFrame
        Original dataframe that contains a column of non-harmonized country names.
    countries_file : str
        Path to json file containing a mapping from non-harmonized to harmonized country names.
    excluded_countries_file : str
        Path to json file containing a list of non-harmonized country names to be ignored (i.e. they will not be
        harmonized, and will therefore not be included in the output data).
    country_col : str
        Name of column in df containing non-harmonized country names.
    warn_on_missing_countries : bool
        True to warn about countries that appear in original table but not in countries file.
    make_missing_countries_nan : bool
        True to make nan any country that appears in original dataframe but not in countries file. False to keep their
        original (possibly non-harmonized) names.
    warn_on_unused_countries : bool
        True to warn about countries that appear in countries file but are useless (since they do not appear in original
        dataframe).
    warn_on_unknown_excluded_countries : bool
        True to warn about countries that appear in the list of non-harmonized countries to ignore, but are not found in
        the data.
    show_full_warning : bool
        True to display list of countries in warning messages.

    Returns
    -------
    df_harmonized : pd.DataFrame
        Original dataframe after standardizing the column of country names.

    """
    df_harmonized = df.copy(deep=False)

    # Load country mappings.
    countries = load_json(countries_file, warn_on_duplicated_keys=True)

    if excluded_countries_file is not None:
        # Load list of excluded countries.
        excluded_countries = load_json(
            excluded_countries_file, warn_on_duplicated_keys=True
        )

        # Check that all countries to be excluded exist in the data.
        unknown_excluded_countries = set(excluded_countries) - set(df[country_col])
        if warn_on_unknown_excluded_countries and (len(unknown_excluded_countries) > 0):
            warn_on_list_of_entities(
                list_of_entities=unknown_excluded_countries,
                warning_message="Unknown country names in excluded countries file:",
                show_list=show_full_warning,
            )

        # Remove rows corresponding to countries to be excluded.
        df_harmonized = df_harmonized[
            ~df_harmonized[country_col].isin(excluded_countries)
        ]

    # Harmonize all remaining country names.
    df_harmonized[country_col] = map_series(
        series=df_harmonized[country_col],
        mapping=countries,
        make_unmapped_values_nan=make_missing_countries_nan,
        warn_on_missing_mappings=warn_on_missing_countries,
        warn_on_unused_mappings=warn_on_unused_countries,
        show_full_warning=show_full_warning,
    )

    return df_harmonized
