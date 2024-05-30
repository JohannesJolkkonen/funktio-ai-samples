import pandas as pd
from db import get_db_connection, get_db_cursor, get_table_info

conn = get_db_connection()
cur = get_db_cursor(conn)

bitcoin_data = pd.read_csv("data/bitcoin_data.csv", delimiter=";")
ethereum_data = pd.read_csv("data/ethereum_data.csv", delimiter=";")
solana_data = pd.read_csv("data/solana_data.csv", delimiter=";")

bitcoin_data["Symbol"] = "BTC"
ethereum_data["Symbol"] = "ETH"
solana_data["Symbol"] = "SOL"

combined_data = pd.concat([bitcoin_data, ethereum_data, solana_data], ignore_index=True)

create_tbl_query = """
DROP TABLE IF EXISTS crypto_data;
CREATE TABLE IF NOT EXISTS crypto_data (
    Date DATE,
    High NUMERIC,
    Low NUMERIC,
    Close NUMERIC,
    Volume NUMERIC,
    Symbol VARCHAR(10)
);
COMMENT ON COLUMN crypto_data.Date IS 'The date of the data point';
COMMENT ON COLUMN crypto_data.High IS 'The high price for the crypto on the date';
COMMENT ON COLUMN crypto_data.Low IS 'The low price for the crypto on the date';
COMMENT ON COLUMN crypto_data.Close IS 'The closing price for the crypto on the date';
COMMENT ON COLUMN crypto_data.Volume IS 'The trading volume on the date';
COMMENT ON COLUMN crypto_data.Symbol IS 'The trading symbol of the cryptocurrency, either. BTC, ETH or SOL';
"""

create_hypertable_query = """
SELECT create_hypertable('crypto_data', by_range('date'));
"""

cur.execute(create_tbl_query)
cur.execute(create_hypertable_query)

for i, row in combined_data.iterrows():
    print(f"Inserting row {i} out of {len(combined_data)}")
    insert_query = f"""
    INSERT INTO crypto_data (Date, High, Low, Close, Volume, Symbol)
    VALUES
    ('{row['timestamp'][:10]}',
    {str(row['high'])},
    {str(row['low'])},
    {str(row['close'])},
    '{str(row['volume'])}',
    '{row['Symbol']}');
    """
    cur.execute(insert_query)

conn.commit()

print(get_table_info(cur, "crypto_data"))

