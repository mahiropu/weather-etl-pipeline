# Weather ETL Pipeline

A small, end-to-end **batch ETL pipeline** built in Python. It pulls hourly weather
data from a public API, cleans and validates it with pandas, and loads it into a
SQLite data warehouse that you can query with SQL.

Built as a portfolio project for a **Data Engineering internship** — the focus is on
showing the fundamentals done properly, not on exotic tooling.

---

## What it demonstrates

| Concept | Where it shows up |
|---|---|
| ETL separation of concerns | `src/extract.py`, `src/transform.py`, `src/load.py` |
| Raw → processed layering | Raw JSON kept in `data/raw/`, clean CSV in `data/processed/` |
| Data modelling | Dimension + fact tables in `sql/schema.sql` |
| Idempotent loads | `INSERT ... ON CONFLICT DO UPDATE` upserts, safe to re-run |
| Data quality checks | Null drops, dedupe, and range validation in `transform.py` |
| Pipeline observability | Structured logs + an `etl_run_log` audit table |
| Error handling | Retry with backoff on API calls, failed runs recorded as `FAILED` |
| Configuration over hardcoding | Cities, paths and API settings live in `config.yaml` |
| Testing | 7 pytest unit tests covering the transform rules |
| Analytics | Four SQL queries in `sql/analytics_queries.sql` |

---

## Architecture

```
  Open-Meteo API
        |
        v
   [ EXTRACT ]  --->  data/raw/*.json         (immutable raw layer)
        |
        v
  [ TRANSFORM ]  --->  data/processed/*.csv   (clean, validated snapshot)
        |
        v
    [ LOAD ]  --->  warehouse.db              (SQLite: dim_city + fact_weather_hourly)
        |
        v
   [ REPORT ]  --->  SQL analytics printed to the console
```

Every run is written to the `etl_run_log` table with start time, end time, status
and row counts, so you can always see what happened and when.

---

## Data source

[Open-Meteo](https://open-meteo.com/) — a free weather API that needs **no API key**,
so this project runs anywhere with no signup. It returns hourly temperature,
humidity, wind speed and precipitation for the last 7 days per city.

Cities pulled by default: Dhaka, Brussels, London, Tokyo, New York.
Add or remove them in `config.yaml` — no code changes needed.

---

## Data model

**`dim_city`** — one row per city (name, country, latitude, longitude).

**`fact_weather_hourly`** — one row per city per hour:

| Column | Type | Description |
|---|---|---|
| `city_name`, `country` | TEXT | Which city the reading belongs to |
| `observed_at` | TEXT | ISO-8601 UTC timestamp |
| `observed_date` | TEXT | `YYYY-MM-DD`, for easy grouping |
| `observed_hour` | INTEGER | 0–23, for time-of-day analysis |
| `temperature_c` | REAL | Temperature in °C |
| `humidity_pct` | REAL | Relative humidity, 0–100 |
| `wind_speed_kmh` | REAL | Wind speed in km/h |
| `precipitation_mm` | REAL | Rainfall in mm |
| `loaded_at` | TEXT | When the row was written by the pipeline |

Primary key is `(city_name, country, observed_at)`, which is what makes re-running
the pipeline safe — existing hours are updated instead of duplicated.

**`etl_run_log`** — one row per pipeline run for auditing.

---

## Quick start

```bash
# 1. Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Run the pipeline (extract -> transform -> load)
python -m src.pipeline

# 3. See the analytics
python -m src.report

# 4. Run the tests
python -m pytest -v
```

Or use the Makefile shortcuts: `make install`, `make run`, `make report`, `make test`, `make clean`.

---

## Example output

Pipeline run:

```
2026-09-13 15:50:36 | INFO | db        | Schema ready
2026-09-13 15:50:36 | INFO | pipeline  | === ETL run 1 started ===
2026-09-13 15:50:36 | INFO | extract   | Extracting Dhaka, BD
2026-09-13 15:50:37 | INFO | extract   | Extracted 5 city payloads
2026-09-13 15:50:37 | INFO | transform | Flattened 960 raw hourly rows
2026-09-13 15:50:37 | INFO | transform | Clean dataset has 960 rows
2026-09-13 15:50:38 | INFO | load      | Upserted 960 rows into fact_weather_hourly
2026-09-13 15:50:38 | INFO | pipeline  | === ETL run 1 finished: 960 rows loaded ===
```

Analytics report:

```
=== Query 1 ===
city_name country  avg_temp_c  min_temp_c  max_temp_c  hours_recorded
    Dhaka      BD       28.66        24.7        33.3             192
 New York      US       22.42        15.0        31.4             192
    Tokyo      JP       22.26        17.9        30.7             192
 Brussels      BE       18.91        12.4        28.9             192
   London      GB       18.47        12.0        26.7             192
```

---

## Data quality rules

Applied in `src/transform.py` before anything reaches the warehouse:

1. **Missing values** — rows with no timestamp or no temperature are dropped.
2. **Duplicates** — deduped on `(city, country, timestamp)`, keeping the latest.
3. **Range checks** — values outside physically plausible bounds are removed:
   temperature −90…60 °C, humidity 0…100 %, wind 0…500 km/h, rain 0…500 mm.
4. **Type safety** — all numeric fields are coerced with `errors="coerce"` so bad
   strings become nulls rather than crashing the run.

Every drop is logged with a count, so silent data loss is impossible.

---

## Project layout

```
weather-etl-pipeline/
├── config.yaml              # Cities, API settings, file paths
├── requirements.txt
├── Makefile
├── src/
│   ├── extract.py           # API calls + retry, writes raw JSON
│   ├── transform.py         # Flatten, clean, validate with pandas
│   ├── load.py              # Idempotent upserts into SQLite
│   ├── db.py                # Connection, schema bootstrap, run logging
│   ├── pipeline.py          # Orchestrates E -> T -> L
│   ├── report.py            # Runs the analytics queries
│   └── utils.py             # Config loading and logging setup
├── sql/
│   ├── schema.sql           # Tables and indexes
│   └── analytics_queries.sql
├── tests/
│   └── test_transform.py    # 7 unit tests on the cleaning rules
├── data/
│   ├── raw/                 # Immutable API payloads, one file per city per run
│   └── processed/           # Cleaned CSV snapshot
└── logs/
    └── pipeline.log
```

---

## Scheduling it

The pipeline is a plain Python module, so any scheduler can run it. Daily at 6am
with cron:

```
0 6 * * * cd /path/to/weather-etl-pipeline && .venv/bin/python -m src.pipeline
```

---

## Possible next steps

Ideas for extending this if you want to go further:

- Swap SQLite for PostgreSQL and load with `SQLAlchemy`
- Orchestrate with Apache Airflow or Prefect instead of cron
- Add dbt models on top of the fact table
- Push the processed CSV to S3 as a cloud data lake layer
- Build a small Streamlit dashboard on the warehouse

---

## Tech stack

Python 3 · pandas · requests · SQLite · PyYAML · pytest
