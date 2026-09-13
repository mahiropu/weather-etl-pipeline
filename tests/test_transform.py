from src.transform import clean, flatten_payload


def make_payload():
    return {
        "_city_name": "Dhaka",
        "_country": "BD",
        "hourly": {
            "time": ["2026-09-01T00:00", "2026-09-01T01:00"],
            "temperature_2m": [28.5, 29.1],
            "relative_humidity_2m": [80, 78],
            "wind_speed_10m": [12.0, 13.5],
            "precipitation": [0.0, 1.2],
        },
    }


def test_flatten_payload_renames_columns():
    df = flatten_payload(make_payload())

    assert list(df.columns) == [
        "observed_at",
        "temperature_c",
        "humidity_pct",
        "wind_speed_kmh",
        "precipitation_mm",
        "city_name",
        "country",
    ]
    assert len(df) == 2


def test_flatten_payload_adds_city_and_country():
    df = flatten_payload(make_payload())

    assert df["city_name"].tolist() == ["Dhaka", "Dhaka"]
    assert df["country"].tolist() == ["BD", "BD"]


def test_clean_adds_date_and_hour():
    df = clean(flatten_payload(make_payload()))

    assert df["observed_date"].tolist() == ["2026-09-01", "2026-09-01"]
    assert df["observed_hour"].tolist() == [0, 1]


def test_clean_drops_missing_temperature():
    payload = make_payload()
    payload["hourly"]["temperature_2m"] = [28.5, None]

    df = clean(flatten_payload(payload))

    assert len(df) == 1


def test_clean_drops_impossible_temperature():
    payload = make_payload()
    payload["hourly"]["temperature_2m"] = [28.5, 999.0]

    df = clean(flatten_payload(payload))

    assert df["temperature_c"].tolist() == [28.5]


def test_clean_drops_duplicate_timestamps():
    payload = make_payload()
    payload["hourly"]["time"] = ["2026-09-01T00:00", "2026-09-01T00:00"]

    df = clean(flatten_payload(payload))

    assert len(df) == 1


def test_clean_column_order():
    df = clean(flatten_payload(make_payload()))

    assert list(df.columns) == [
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
