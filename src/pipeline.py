import sys

from src import db
from src.extract import extract
from src.load import load
from src.transform import transform
from src.utils import get_logger, load_config, utc_now

logger = get_logger("pipeline")


def run():
    config = load_config()
    connection = db.connect(config)
    db.init_schema(connection, config)

    run_id = db.start_run(connection, utc_now())
    logger.info("=== ETL run %s started ===", run_id)

    try:
        payloads = extract(config)
        df = transform(payloads, config)
        rows_loaded = load(connection, df, config)

        db.finish_run(connection, run_id, utc_now(), "SUCCESS", len(df), rows_loaded, "ok")
        logger.info("=== ETL run %s finished: %s rows loaded ===", run_id, rows_loaded)
        return 0

    except Exception as error:
        logger.exception("ETL run %s failed", run_id)
        db.finish_run(connection, run_id, utc_now(), "FAILED", message=str(error))
        return 1

    finally:
        connection.close()


if __name__ == "__main__":
    sys.exit(run())
