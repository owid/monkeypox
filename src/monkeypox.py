import datetime

import pandas as pd

from shared import harmonize_countries, list_countries_in_region

SOURCE_MONKEYPOX = (
    "https://frontdoor-l4uikgap6gz3m.azurefd.net/MPX/V_MPX_VALIDATED_DAILY?&$format=csv"
)
SOURCE_COUNTRY_MAPPING = "country_mapping.json"
SOURCE_POPULATION = "https://github.com/owid/covid-19-data/raw/master/scripts/input/un/population_latest.csv"
OUTPUT_FILE = "owid-monkeypox-data.csv"
WHO_REGIONS = ["EURO", "AMRO", "WPRO", "EMRO", "AFRO", "SEARO"]


def import_data() -> pd.DataFrame:
    df = pd.DataFrame()
    # Fetching the data for each WHO region separately
    for region in WHO_REGIONS:
        url = f"https://frontdoor-l4uikgap6gz3m.azurefd.net/MPX/V_MPX_VALIDATED_DAILY?&$format=csv&$filter=WHO_REGION%20eq%20%27{region}%27"
        df_region = pd.read_csv(url)
        df = pd.concat([df, df_region])
    return df


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df[["COUNTRY", "DATE", "TOTAL_CONF_CASES", "TOTAL_CONF_DEATHS"]].rename(
        columns={
            "COUNTRY": "location",
            "DATE": "date",
            "TOTAL_CONF_CASES": "total_cases",
            "TOTAL_CONF_DEATHS": "total_deaths",
        }
    )


def mpox_harmonize_countries(df: pd.DataFrame) -> pd.DataFrame:
    return harmonize_countries(
        df,
        countries_file=SOURCE_COUNTRY_MAPPING,
        country_col="location",
        warn_on_missing_countries=False,
    )


def clean_date(df: pd.DataFrame) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df.date).dt.date.astype(str)
    return df


def clean_values(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("date", ascending=False)
    df["total_cases"] = df[["location", "total_cases"]].groupby("location").cummin()
    df["total_deaths"] = df[["location", "total_deaths"]].groupby("location").cummin()
    return df.sort_values(["location", "date"])


def explode_dates(df: pd.DataFrame) -> pd.DataFrame:
    df_range = pd.concat(
        [
            pd.DataFrame(
                {
                    "location": location,
                    "date": pd.date_range(
                        start=df.date.min(), end=df.date.max(), freq="D"
                    ).astype(str),
                }
            )
            for location in df.location.unique()
        ]
    )
    df = pd.merge(
        df, df_range, on=["location", "date"], validate="one_to_one", how="right"
    )
    df["report"] = df.total_cases.notnull() | df.total_deaths.notnull()
    return df


def add_world(df: pd.DataFrame) -> pd.DataFrame:
    df[["total_cases", "total_deaths"]] = (
        df[["location", "total_cases", "total_deaths"]]
        .groupby("location")
        .ffill()
        .fillna(0)
    )
    world = (
        df[["date", "total_cases", "total_deaths"]]
        .groupby("date", as_index=False)
        .sum()
        .assign(location="World", report=True)
    )
    world = world[world.date < str(datetime.date.today())]
    return pd.concat([df, world])


def add_regions(df: pd.DataFrame) -> pd.DataFrame:
    # Add region for each country
    for region in [
        "North America",
        "South America",
        "Europe",
        "Asia",
        "Africa",
        "Oceania",
    ]:
        df.loc[
            df.location.isin(list_countries_in_region(region=region)), "region"
        ] = region

    # Calculate regional aggregates
    regions = (
        df[df.region.notnull()][
            ["region", "date", "total_cases", "total_deaths", "report"]
        ]
        .groupby(["region", "date"], as_index=False)
        .agg({"total_cases": "sum", "total_deaths": "sum", "report": "max"})
        .rename(columns={"region": "location"})
    )
    regions = regions[regions.date < str(datetime.date.today())]
    df = df.drop(columns="region")

    # Concatenate with df
    return pd.concat([df, regions])


def add_population_and_countries(df: pd.DataFrame) -> pd.DataFrame:
    pop = pd.read_csv(
        SOURCE_POPULATION, usecols=["entity", "population", "iso_code"]
    ).rename(columns={"entity": "location"})
    missing_locs = set(df.location) - set(pop.location)
    if len(missing_locs) > 0:
        raise Exception(f"Missing location(s) in population file: {missing_locs}")
    df = pd.merge(pop, df, how="right", validate="one_to_many", on="location")
    return df


def derive_metrics(df: pd.DataFrame) -> pd.DataFrame:
    def derive_country_metrics(df: pd.DataFrame) -> pd.DataFrame:
        # Add daily values
        df["new_cases"] = df.total_cases.diff()
        df["new_deaths"] = df.total_deaths.diff()

        # Add 7-day averages
        df["new_cases_smoothed"] = (
            df.new_cases.rolling(window=7, min_periods=7, center=False).mean().round(2)
        )
        df["new_deaths_smoothed"] = (
            df.new_deaths.rolling(window=7, min_periods=7, center=False).mean().round(2)
        )

        # Add per-capita metrics
        df = df.assign(
            new_cases_per_million=round(df.new_cases * 1000000 / df.population, 3),
            total_cases_per_million=round(df.total_cases * 1000000 / df.population, 3),
            new_cases_smoothed_per_million=round(
                df.new_cases_smoothed * 1000000 / df.population, 3
            ),
            new_deaths_per_million=round(df.new_deaths * 1000000 / df.population, 5),
            total_deaths_per_million=round(
                df.total_deaths * 1000000 / df.population, 5
            ),
            new_deaths_smoothed_per_million=round(
                df.new_deaths_smoothed * 1000000 / df.population, 5
            ),
        ).drop(columns="population")

        min_reporting_date = df[df.report].date.min()
        max_reporting_date = df[df.report].date.max()
        df = df[(df.date >= min_reporting_date) & (df.date <= max_reporting_date)].drop(
            columns="report"
        )

        return df

    return df.groupby("iso_code").apply(derive_country_metrics)


def filter_dates(df: pd.DataFrame) -> pd.DataFrame:
    return df[df.date >= "2022-05-01"]


def main():
    (
        import_data()
        .pipe(clean_columns)
        .pipe(mpox_harmonize_countries)
        .pipe(clean_date)
        .pipe(clean_values)
        .pipe(explode_dates)
        .pipe(add_world)
        .pipe(add_regions)
        .pipe(add_population_and_countries)
        .pipe(derive_metrics)
        .pipe(filter_dates)
        .sort_values(["location", "date"])
    ).to_csv(f"../{OUTPUT_FILE}", index=False)


if __name__ == "__main__":
    main()
