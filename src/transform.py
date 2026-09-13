from datetime import datetime, timezone

import pandas as pd

from src.utils import get_logger, resolve

logger = get_logger("transform")

VALID_RANGES = {
    "temperature_c": (-90.0, 60.0),
    "humidity_pct": (0.0, 100.0),
    "wind_speed_kmh": (0.0, 500.0),
    "precipitation_mm": (0.0, 500.0),
}

COLUMN_MAP = {
    "time": "observed_at",
    "temperature_2m": "temperature_c",
    "relative_humidity_2m": "humidity_pct",
    "wind_speed_10m": "wind_speed_kmh",
    "precipitation": "precipitation_mm",
}

FINAL_COLUMNS = [
    "city_name",
    "country",
    "observed_at",
    "observed_date",
    "observed_hour",
    "temperature_c",
    "humidity_pct",
    "wind_speed_kmh",
    "precipitation_mm",
    "loaded_at",
]


def flatten_payload(payload):
    df = pd.DataFrame(payload["hourly"])
    df = df.rename(columns=COLUMN_MAP)
    df["city_name"] = payload["_city_name"]
    df["country"] = payload["_country"]
    return df


def clean(df):
    df = df.copy()

    df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True, errors="coerce")
    for column in VALID_RANGES:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    before = len(df)
    df = df.dropna(subset=["observed_at", "temperature_c"])
    logger.info("Dropped %s rows with missing timestamp or temperature", before - len(df))

    before = len(df)
    df = df.drop_duplicates(subset=["city_name", "country", "observed_at"], keep="last")
    logger.info("Dropped %s duplicate rows", before - len(df))

    for column, (low, high) in VALID_RANGES.items():
        before = len(df)
        df = df[df[column].isna() | df[column].between(low, high)]
        if before - len(df) > 0:
            logger.warning("Dropped %s rows with bad %s", before - len(df), column)

    df["observed_date"] = df["observed_at"].dt.strftime("%Y-%m-%d")
    df["observed_hour"] = df["observed_at"].dt.hour
    df["observed_at"] = df["observed_at"].dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    df["loaded_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    return df[FINAL_COLUMNS].sort_values(["city_name", "observed_at"]).reset_index(drop=True)


def transform(payloads, config):
    frames = []
    for payload in payloads:
        frames.append(flatten_payload(payload))

    df = pd.concat(frames, ignore_index=True)
    logger.info("Flattened %s raw hourly rows", len(df))

    df = clean(df)
    logger.info("Clean dataset has %s rows", len(df))

    processed_dir = resolve(config["paths"]["processed_dir"])
    processed_dir.mkdir(parents=True, exist_ok=True)
    path = processed_dir / "weather_hourly.csv"
    df.to_csv(path, index=False)
    logger.info("Wrote processed snapshot to %s", path.name)

    return df
