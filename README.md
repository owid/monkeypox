# Mpox data

⚠️ This dataset no longer powers our [Mpox Data Explorer](https://ourworldindata.org/explorers/monkeypox). The data pipeline has now been moved to our [ETL system](https://github.com/owid/etl), and the resulting data file can be found [here (CSV file)](https://catalog.ourworldindata.org/explorers/who/latest/monkeypox/monkeypox.csv) (CSV in this repository is still updated, but fetching from the ETL system is recommended).

As of August 2024, we are using data produced by the World Health Organization for _confirmed_ cases and deaths and data from the African CDC for _suspected_ cases. We are closely monitoring the ongoing mpox situation in Central Africa. Any changes to our data sources will be documented here.

----

### 2024-08-29 - Analyzing the data produced by the World Health Organization on the 2022 mpox outbreak

Data on the 2022 mpox outbreak is collated by the [World Health Organization](https://extranet.who.int/publicemergency/), and is updated as new information is reported.

We fetch the latest version of the WHO data every hour, keep records up to the previous day, apply some transformations (7-day averages, per-capita adjustments, etc.), and produce the `owid-monkeypox-data.csv` file in this repository. This file powers our [Mpox Data Explorer](https://ourworldindata.org/monkeypox) on Our World in Data.


### 2022-09-23 - Previous versions of the data - using Global.health

This repository previously relied on data collated by the team at [Global.health](https://www.global.health/). On 23 September 2022, the Global.health team started aggregating data from openly-available data resources (including the WHO) instead of collating data itself. Following this change, we started fetching data directly from the WHO.
