from src.utils import get_logger

logger = get_logger("load")

UPSERT_CITY = """
INSERT INTO dim_city (city_name, country, latitude, longitude)
VALUES (?, ?, ?, ?)
ON CONFLICT (city_name, country) DO UPDATE SET
    latitude = excluded.latitude,
    longitude = excluded.longitude
"""

UPSERT_WEATHER = """
INSERT INTO fact_weather_hourly (
    city_name, country, observed_at, observed_date, observed_hour,
    temperature_c, humidity_pct, wind_speed_kmh, precipitation_mm, loaded_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (city_name, country, observed_at) DO UPDATE SET
    temperature_c = excluded.temperature_c,
    humidity_pct = excluded.humidity_pct,
    wind_speed_kmh = excluded.wind_speed_kmh,
    precipitation_mm = excluded.precipitation_mm,
    loaded_at = excluded.loaded_at
"""


def load_cities(connection, config):
    rows = []
    for city in config["cities"]:
        rows.append((city["name"], city["country"], city["latitude"], city["longitude"]))

    connection.executemany(UPSERT_CITY, rows)
    connection.commit()
    logger.info("Upserted %s cities into dim_city", len(rows))


def load_weather(connection, df):
    rows = list(df.itertuples(index=False, name=None))
    connection.executemany(UPSERT_WEATHER, rows)
    connection.commit()
    logger.info("Upserted %s rows into fact_weather_hourly", len(rows))
    return len(rows)


def load(connection, df, config):
    load_cities(connection, config)
    return load_weather(connection, df)
