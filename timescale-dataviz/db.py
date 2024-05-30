import psycopg2
from psycopg2 import extras
from decouple import config

CONNECTION = config("TIMESCALE_CONN")

def get_db_connection():
    conn = psycopg2.connect(
        dsn=CONNECTION,
        cursor_factory=extras.DictCursor,
    )
    return conn

def get_db_cursor(conn):
    cur = conn.cursor()
    return cur


def get_table_info(cur, table_name):
    table_info = f"### Table: {table_name}\n"
    cur.execute(
        f"""
        SELECT 
            c.column_name,
            c.data_type,
            d.description as col_description 
        FROM 
            information_schema.columns c 
        LEFT JOIN
            pg_description d ON c.table_name::regclass = d.objoid and c.ordinal_position = d.objsubid
        WHERE c.table_schema = 'public' AND c.table_name = '{table_name}'
        ORDER BY
            c.ordinal_position
    """
    )
    for row in cur.fetchall():
        table_info += f"col_name: {row['column_name']}, dtype: {row['data_type']}, description: {row['col_description']}\n"
    return table_info
