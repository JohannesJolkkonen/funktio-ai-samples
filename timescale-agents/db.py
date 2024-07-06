import psycopg2
from psycopg2 import extras
from decouple import config
from pydantic import BaseModel
from datetime import datetime
import pandas as pd

CONNECTION = config("TIMESCALE_CONN")


class SensorData(BaseModel):
    sensor_id: str
    timestamp: datetime
    temperature: float
    humidity: float


def get_db_connection():
    conn = psycopg2.connect(
        dsn=CONNECTION,
        cursor_factory=extras.DictCursor,
    )
    return conn


def get_db_cursor(conn):
    cur = conn.cursor()
    return cur


def _create_sensor_table(cur):
    cur.execute(
        """
        DROP TABLE IF EXISTS sensor_data;
        CREATE TABLE IF NOT EXISTS sensor_data (
            sensor_id TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL
        )
        """
    )


def _create_log_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS log_data (
            timestamp TIMESTAMP NOT NULL,
            message TEXT NOT NULL
        )
    """
    )


def _create_agent_messages_table(cur):
    cur.execute(
        """
        DROP TABLE IF EXISTS agent_messages;
        CREATE TABLE IF NOT EXISTS agent_messages (
            timestamp TIMESTAMP NOT NULL,
            message TEXT NOT NULL
        )
    """
    )


def create_tables(cur):
    _create_sensor_table(cur)
    _create_log_table(cur)
    _create_agent_messages_table(cur)


def insert_sensor_data(cur, sensor_data: SensorData):
    cur.execute(
        """
        INSERT INTO sensor_data (sensor_id, timestamp, temperature, humidity) VALUES (%s, %s, %s, %s)
        """,
        (
            sensor_data.sensor_id,
            sensor_data.timestamp,
            sensor_data.temperature,
            sensor_data.humidity,
        ),
    )


def insert_log_data(cur, msg: str):
    cur.execute(
        f"""
        INSERT INTO log_data (timestamp, message) VALUES (%s, %s)
        """,
        (datetime.now(), msg),
    )


def insert_agent_message(cur, msg: str):
    cur.execute(
        f"""
        INSERT INTO agent_messages (timestamp, message) VALUES (%s, %s)
        """,
        (datetime.now(), msg),
    )


def read_sensor_data(cur) -> pd.DataFrame:
    cur.execute(
        """
        SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 25
        """,
        (),
    )
    rows = cur.fetchall()
    return pd.DataFrame(
        rows, columns=["sensor_id", "timestamp", "temperature", "humidity"]
    )


def read_log_data(cur, n_rows) -> pd.DataFrame:
    cur.execute(
        f"""
        SELECT * FROM log_data ORDER BY timestamp DESC LIMIT {n_rows}
        """,
        (),
    )
    rows = cur.fetchall()
    return pd.DataFrame(rows, columns=["timestamp", "message"])


def read_agent_messages(cur, n_rows) -> pd.DataFrame:
    cur.execute(
        f"""
        SELECT * FROM agent_messages ORDER BY timestamp DESC LIMIT {n_rows}
        """,
        (),
    )
    rows = cur.fetchall()
    return pd.DataFrame(rows, columns=["timestamp", "message"])
