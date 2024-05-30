import plotly.graph_objects as go
import pandas as pd
from forecasting import forecast_future_values

def get_bar_chart(data, title, barmode="group"):
    traces = []
    cryptos = sorted(set([d["symbol"] for d in data]))
    dates = sorted([d[0] for d in data])
    for crypto in cryptos:
        values = []
        for date in dates:
            filtered_data = [
                d for d in data if d["symbol"] == crypto and d["date"] == date
            ]
            if filtered_data:
                values.append(filtered_data[0]["value"])
            else:
                values.append(0)

        traces.append(
            go.Bar(name=crypto, x=dates, y=values, offsetgroup=cryptos.index(crypto))
        )

    fig = go.Figure(data=traces)
    fig.update_layout(
        barmode=barmode,
        title=title,
        xaxis_title="Date",
        yaxis_title="Value",
        legend_title="Type",
    )
    return fig


def get_pie_chart(data, title):
    values = [d["value"] for d in data]
    labels = [d["symbol"] for d in data]

    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4)])
    fig.update_layout(
        title_text=title,
    )
    return fig


def get_forecast_chart(data, title, cols, n_days, model):
    past_df, forecast = forecast_future_values(data, cols, n_days, model)

    past_trace = go.Scatter(
        x=past_df.index,
        y=past_df["value"],
        mode="lines",
        name="Past Data",
        line=dict(color="blue"),
    )

    forecast_trace = go.Scatter(
        x=forecast.index,
        y=forecast.values,
        mode="lines",
        name="Forecast",
        line=dict(color="red", dash="dash"),
    )

    # Create the layout for the plot
    layout = go.Layout(
        title=title, xaxis=dict(title="Date"), yaxis=dict(title="Price")
    )

    # Create the figure and add the traces and layout
    fig = go.Figure(data=[past_trace, forecast_trace], layout=layout)

    # Display the plot
    return fig
