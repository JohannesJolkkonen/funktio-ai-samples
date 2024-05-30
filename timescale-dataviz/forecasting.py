import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from db import get_db_cursor, get_db_connection

conn = get_db_connection()
cur = get_db_cursor(conn)


def forecast_future_values(data, cols, n_days, model):
    """
    Project future values for n days ahead, using the selected model
    """
    df = pd.DataFrame.from_records(data, columns=cols)
    df["date"] = pd.to_datetime(df["date"])
    df.sort_values("date", inplace=True)
    df.set_index("date", inplace=True)

    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    # Fit the model
    if model == "arima":
        model = ARIMA(df["value"], order=(1, 2, 4))
    elif model == "exponential":
        model = ExponentialSmoothing(
            df["value"], seasonal_periods=7, trend="additive", seasonal="additive"
        )

    fit = model.fit()

    # Forecast future prices
    forecast = fit.forecast(steps=n_days)
    random_multipliers = np.random.uniform(0.98, 1.03, size=n_days)
    forecast = forecast * random_multipliers

    # Join the last value of the past data to forecast, for continuity when plotting
    last_date = df.index[-1]
    last_value = df.iloc[-1]["value"]
    last_value_series = pd.Series([last_value], index=[last_date])
    forecast_dates = pd.date_range(
        start=last_date + pd.DateOffset(days=1), periods=n_days
    )
    forecast = pd.Series(forecast, index=forecast_dates)

    forecast = pd.concat([last_value_series, forecast])

    return df, forecast
