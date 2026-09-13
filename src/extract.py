import json
import time
from datetime import datetime, timezone

import requests

from src.utils import get_logger, resolve, utc_now

logger = get_logger("extract")

HOURLY_FIELDS = "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation"


def fetch_city(city, config):
    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "hourly": HOURLY_FIELDS,
        "past_days": config["past_days"],
        "forecast_days": 1,
        "timezone": "UTC",
    }

    response = requests.get(config["api"]["base_url"], params=params, timeout=config["api"]["timeout_seconds"])
    response.raise_for_status()

    data = response.json()
    data["_city_name"] = city["name"]
    data["_country"] = city["country"]
    data["_extracted_at"] = utc_now()
    return data


def fetch_with_retry(city, config, attempts=3):
    for attempt in range(1, attempts + 1):
        try:
            return fetch_city(city, config)
        except requests.RequestException as error:
            logger.warning("Fetch failed for %s (attempt %s/%s): %s", city["name"], attempt, attempts, error)
            if attempt == attempts:
                raise
            time.sleep(2 ** attempt)


def extract(config):
    raw_dir = resolve(config["paths"]["raw_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payloads = []

    for city in config["cities"]:
        logger.info("Extracting %s, %s", city["name"], city["country"])
        data = fetch_with_retry(city, config)

        name = city["name"].lower().replace(" ", "_")
        path = raw_dir / f"{name}_{stamp}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info("Saved raw payload to %s", path.name)
        payloads.append(data)

    logger.info("Extracted %s city payloads", len(payloads))
    return payloads
