SELECT
    city_name,
    country,
    ROUND(AVG(temperature_c), 2) AS avg_temp_c,
    ROUND(MIN(temperature_c), 2) AS min_temp_c,
    ROUND(MAX(temperature_c), 2) AS max_temp_c,
    COUNT(*) AS hours_recorded
FROM fact_weather_hourly
GROUP BY city_name, country
ORDER BY avg_temp_c DESC;

SELECT
    city_name,
    observed_date,
    ROUND(MAX(temperature_c), 2) AS peak_temp_c
FROM fact_weather_hourly
GROUP BY city_name, observed_date
HAVING peak_temp_c = (
    SELECT MAX(temperature_c)
    FROM fact_weather_hourly f2
    WHERE f2.city_name = fact_weather_hourly.city_name
)
ORDER BY peak_temp_c DESC;

SELECT
    city_name,
    observed_date,
    ROUND(SUM(precipitation_mm), 2) AS total_rain_mm
FROM fact_weather_hourly
GROUP BY city_name, observed_date
ORDER BY total_rain_mm DESC
LIMIT 10;

SELECT
    observed_hour,
    ROUND(AVG(temperature_c), 2) AS avg_temp_c
FROM fact_weather_hourly
GROUP BY observed_hour
ORDER BY observed_hour;
