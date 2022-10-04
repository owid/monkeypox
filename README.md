# Monkeypox Data

### Analyzing the data produced by the World Health Organization on the 2022 monkeypox outbreak

Data on the 2022 monkeypox outbreak is collated by the [World Health Organization](https://extranet.who.int/publicemergency/), and is updated as new information is reported.

We fetch the latest version of the WHO data every hour, keep records up to the previous day, apply some transformations (7-day averages, per-capita adjustments, etc.), and produce the `owid-monkeypox-data.csv` file in this repository. This file powers our [Monkeypox Data Explorer](https://ourworldindata.org/monkeypox) on Our World in Data.

----

### Previous versions of the data

This repository previously relied on data collated by the team at [Global.health](https://www.global.health/). On 23 September 2022, the Global.health team started aggregating data from openly-available data resources (including the WHO) instead of collating data itself. Following this change, we started fetching data directly from the WHO.
