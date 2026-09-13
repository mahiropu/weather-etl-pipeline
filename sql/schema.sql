CREATE TABLE IF NOT EXISTS dim_city (
    city_id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_name TEXT NOT NULL,
    country TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    UNIQUE (city_name, country)
);

CREATE TABLE IF NOT EXISTS fact_weather_hourly (
    city_name TEXT NOT NULL,
    country TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    observed_date TEXT NOT NULL,
    observed_hour INTEGER NOT NULL,
    temperature_c REAL,
    humidity_pct REAL,
    wind_speed_kmh REAL,
    precipitation_mm REAL,
    loaded_at TEXT NOT NULL,
    PRIMARY KEY (city_name, country, observed_at)
);

CREATE INDEX IF NOT EXISTS idx_fact_weather_date ON fact_weather_hourly (observed_date);

CREATE INDEX IF NOT EXISTS idx_fact_weather_city ON fact_weather_hourly (city_name);

CREATE TABLE IF NOT EXISTS etl_run_log (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    rows_extracted INTEGER DEFAULT 0,
    rows_loaded INTEGER DEFAULT 0,
    message TEXT
);
