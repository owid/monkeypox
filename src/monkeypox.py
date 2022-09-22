import datetime
import requests

import pandas as pd

SOURCE_MONKEYPOX = "https://extranet.who.int/publicemergency/api/Monkeypox/"
SOURCE_COUNTRY_MAPPING = "country_mapping.csv"
SOURCE_POPULATION = "https://github.com/owid/covid-19-data/raw/master/scripts/input/un/population_latest.csv"
OUTPUT_FILE = "owid-monkeypox-data.csv"


def import_data(url: str) -> pd.DataFrame:
    data = requests.post(url).json()
    df = pd.DataFrame.from_records(data["Data"])
    return df


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df[["ISO3", "DATEREP", "TOTAL_CONFCASES", "TOTAL_ConfDeaths"]].rename(
        columns={
            "ISO3": "iso_code",
            "DATEREP": "date",
            "TOTAL_CONFCASES": "total_cases",
            "TOTAL_ConfDeaths": "total_deaths",
        }
    )


def clean_date(df: pd.DataFrame) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df.date).dt.date.astype(str)
    return df


def clean_values(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("date", ascending=False)
    df["total_cases"] = df[["iso_code", "total_cases"]].groupby("iso_code").cummin()
    df["total_deaths"] = df[["iso_code", "total_deaths"]].groupby("iso_code").cummin()
    return df.sort_values(["iso_code", "date"])


def explode_dates(df: pd.DataFrame) -> pd.DataFrame:
    df_range = pd.concat(
        [
            pd.DataFrame(
                {
                    "iso_code": iso_code,
                    "date": pd.date_range(
                        start=df.date.min(), end=df.date.max(), freq="D"
                    ).astype(str),
                }
            )
            for iso_code in df.iso_code.unique()
        ]
    )
    df = pd.merge(
        df, df_range, on=["iso_code", "date"], validate="one_to_one", how="right"
    )
    df["report"] = df.total_cases.notnull() | df.total_deaths.notnull()
    return df


def add_world(df: pd.DataFrame) -> pd.DataFrame:
    df[["total_cases", "total_deaths"]] = (
        df[["iso_code", "total_cases", "total_deaths"]]
        .groupby("iso_code")
        .ffill()
        .fillna(0)
    )
    world = (
        df[["date", "total_cases", "total_deaths"]]
        .groupby("date", as_index=False)
        .sum()
        .assign(iso_code="OWID_WRL", report=True)
    )
    return pd.concat([df, world])


def add_population_and_countries(df: pd.DataFrame) -> pd.DataFrame:
    pop = pd.read_csv(
        SOURCE_POPULATION, usecols=["entity", "population", "iso_code"]
    ).rename(columns={"entity": "location", "iso_code": "iso_code"})
    missing_iso = set(df.iso_code) - set(pop.iso_code)
    if len(missing_iso) > 0:
        raise Exception(f"Missing ISO in population file: {missing_iso}")
    df = pd.merge(pop, df, how="right", validate="one_to_many", on="iso_code")
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
            new_deaths_per_million=round(df.new_deaths * 1000000 / df.population, 3),
            total_deaths_per_million=round(
                df.total_deaths * 1000000 / df.population, 3
            ),
            new_deaths_smoothed_per_million=round(
                df.new_deaths_smoothed * 1000000 / df.population, 3
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
    return df[(df.date >= "2022-05-01") & (df.date < str(datetime.date.today()))]


def main():
    (
        import_data(SOURCE_MONKEYPOX)
        .pipe(clean_columns)
        .pipe(clean_date)
        .pipe(clean_values)
        .pipe(explode_dates)
        .pipe(add_world)
        .pipe(add_population_and_countries)
        .pipe(derive_metrics)
        .pipe(filter_dates)
        .sort_values(["location", "date"])
    ).to_csv(f"../{OUTPUT_FILE}", index=False)


if __name__ == "__main__":
    main()
