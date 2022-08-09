# Monkeypox Data

### Analyzing the data produced by the Global.health team on the 2022 monkeypox outbreak

Data on the 2022 monkeypox outbreak is collated by the team at [Global.health](https://www.global.health/), and is updated as new information is reported.

We fetch the latest version of the Global.health data every hour, keep records up to the previous day, apply some transformations (7-day averages, per-capita adjustments, etc.), and produce the `owid-monkeypox-data.csv` file in this repository. This file powers our [Monkeypox Data Explorer](https://ourworldindata.org/monkeypox) on Our World in Data.

Global.health compiles data exclusively from publicly-available information. Sources for each case are listed [here](https://github.com/globaldothealth/monkeypox/blob/main/latest.csv). Should you identify any inconsistencies in the data or have additional information or questions, please get in touch with them [here](https://github.com/globaldothealth/monkeypox/issues).

They also maintain a data dictionary and several machine-readable files [in their own GitHub repository](https://github.com/globaldothealth/monkeypox). Please check permissions before publishing this data and refer back to each source and the global.health team if you decide to so: _Global.health Monkeypox (accessed on YYYY-MM-DD)._
