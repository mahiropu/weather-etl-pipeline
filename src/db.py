import sqlite3

from src.utils import get_logger, resolve

logger = get_logger("db")


def connect(config):
    connection = sqlite3.connect(resolve(config["paths"]["database"]))
    connection.row_factory = sqlite3.Row
    return connection


def init_schema(connection, config):
    with open(resolve(config["paths"]["schema"])) as f:
        connection.executescript(f.read())
    connection.commit()
    logger.info("Schema ready")


def start_run(connection, started_at):
    cursor = connection.execute(
        "INSERT INTO etl_run_log (started_at, status) VALUES (?, 'RUNNING')",
        (started_at,),
    )
    connection.commit()
    return cursor.lastrowid


def finish_run(connection, run_id, finished_at, status, rows_extracted=0, rows_loaded=0, message=""):
    connection.execute(
        """
        UPDATE etl_run_log
        SET finished_at = ?, status = ?, rows_extracted = ?, rows_loaded = ?, message = ?
        WHERE run_id = ?
        """,
        (finished_at, status, rows_extracted, rows_loaded, message, run_id),
    )
    connection.commit()
