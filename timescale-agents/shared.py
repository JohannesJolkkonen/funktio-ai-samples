from shiny import module, reactive, render, ui
import plotly.express as px
from db import (
    read_sensor_data,
    get_db_cursor,
    get_db_connection,
    read_log_data,
    read_agent_messages,
)
import pandas as pd
from agent import agent_executor
import asyncio
from langchain.schema import AIMessage

conn = get_db_connection()
cur = get_db_cursor(conn)


WARNING_THRESHOLDS = {
    "temperature": 40,  # Example threshold, adjust as needed
    # Add thresholds for other measurements
}


@module.ui
def value_box_ui(title):
    return ui.value_box(
        title,
        ui.output_text("value"),
        showcase=ui.output_ui("icon"),
        style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; height: 120px;",
    )


def last_modified_sensor_data():
    """
    Fast-executing call to get the timestamp of the most recent row in the
    database. We will poll against this in absence of a way to receive a push
    notification when our Timescale database changes.
    """
    cur.execute("SELECT MAX(timestamp) FROM sensor_data")
    return cur.fetchone()[0]


def last_modified_log_data():
    cur.execute("SELECT MAX(timestamp) FROM log_data")
    return cur.fetchone()[0]


def last_modified_agent_messages():
    cur.execute("SELECT MAX(timestamp) FROM agent_messages")
    return cur.fetchone()[0]


def check_thresholds(data, thresholds):
    if data.empty:
        return None

    for measurement, threshold in thresholds.items():
        if data[measurement].iloc[0] > threshold:
            print(f"{measurement} is above warning threshold of {threshold}")
            return f"{measurement} is above warning threshold of {threshold}"
    return None


@module.server
def value_box_server(input, output, session, data_function, measurement: str):
    @reactive.calc
    def score():
        d = data_function()
        temp = d.iloc[0][measurement]
        return temp

    @render.text
    def value():
        return f"{score()}"


async def invoke_and_stream_agent(input):
    async for chunk in agent_executor.astream({"input": input}):
        messages = chunk.get("messages")
        for message in messages:
            if isinstance(message, AIMessage):
                print(message.content)
                if message.content:
                    yield message.content
        await asyncio.sleep(0.1)


@reactive.poll(last_modified_sensor_data)
def df():
    """
    @reactive.poll calls a cheap query ('last_modified()') every 1 second to
    check if it returns a different value. In that case, the expensive query ('df()' will be run and downstream
    calculations updated.

    By declaring this reactive object at the top-level of the script instead of
    in the server function, all sessions are sharing the same object, so the
    expensive query is only run once no matter how many users are connected.
    """
    tbl = read_sensor_data(cur)
    tbl["timestamp"] = pd.to_datetime(tbl["timestamp"], utc=True)
    tbl = tbl.sort_values(by="timestamp", ascending=False)
    # Create a short label for readability
    tbl["time"] = tbl["timestamp"].dt.strftime("%H:%M:%S")
    return tbl


@reactive.poll(last_modified_log_data)
def logs():
    """
    @reactive.poll calls a cheap query ('last_modified()') every 1 second to
    check if it returns a different value. In that case, the expensive query ('df()' will be run and downstream
    calculations updated.

    By declaring this reactive object at the top-level of the script instead of
    in the server function, all sessions are sharing the same object, so the
    expensive query is only run once no matter how many users are connected.
    """
    tbl = read_log_data(cur, 10)
    tbl["timestamp"] = pd.to_datetime(tbl["timestamp"], utc=True)
    tbl = tbl.sort_values(by="timestamp", ascending=False)
    # Create a short label for readability
    tbl["time"] = tbl["timestamp"].dt.strftime("%H:%M:%S")
    return tbl


@reactive.poll(last_modified_agent_messages)
def agent_logs():
    tbl = read_agent_messages(cur, 10)
    tbl["timestamp"] = pd.to_datetime(tbl["timestamp"], utc=True)
    tbl = tbl.sort_values(by="timestamp", ascending=False)
    # Create a short label for readability
    tbl["time"] = tbl["timestamp"].dt.strftime("%H:%M:%S")
    print(tbl.head(10))
    return tbl


THRESHOLD_MID = 40
THRESHOLD_MID_COLOR = "#f9b928"


def plot_timeseries(d: pd.DataFrame):
    min_timestamp = d["timestamp"].min()
    max_timestamp = d["timestamp"].max()
    fig = px.line(
        d,
        x="timestamp",
        y=["temperature", "humidity"],
        labels=dict(temperature="Temperature", humidity="Humidity"),
        color_discrete_sequence=px.colors.qualitative.Set2,
        template="simple_white",
    )

    fig.add_hline(
        THRESHOLD_MID,
        line_dash="dot",
        line=dict(color=THRESHOLD_MID_COLOR, width=2),
        opacity=0.3,
        annotation=dict(text="Danger Zone", xref="paper", x=1, y=THRESHOLD_MID),
        annotation_position="bottom right",
    )

    fig.update_yaxes(range=[0, 90], fixedrange=False)
    fig.update_xaxes(
        range=[min_timestamp, max_timestamp], fixedrange=True, tickangle=60
    )
    fig.update_layout(hovermode="x unified")

    return fig
