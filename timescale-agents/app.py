from shiny import App, Inputs, Outputs, Session, reactive, ui, render
from shinywidgets import render_widget, output_widget
import plotly.express as px
from shared import value_box_ui, value_box_server, plot_timeseries, df, logs, agent_logs, invoke_and_stream_agent, WARNING_THRESHOLDS, check_thresholds
from db import insert_agent_message, get_db_connection, get_db_cursor
import plotly.graph_objects as go
from css import app_ui_css
import requests
import asyncio 
from textwrap import wrap

all_measurements = ["temperature", "humidity"]#, "pressure"]

agent_running = False

app_ui = ui.page_fluid(
    ui.tags.style(app_ui_css),
        ui.page_sidebar(
            ui.sidebar(
            value_box_ui("temperature", "Temperature"),
            value_box_ui("humidity", "Humidity"),
            ui.input_action_button("restart_device", "Restart device"),
            ui.input_action_button("simulate_failure", "Simulate Overheating")
        ),
        ui.card(
            ui.card_header(
            "Sensor readings over time",
            ),
            output_widget(id="plot"),
            full_screen=True
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Sensor logs"),
                ui.output_text_verbatim(id="logs_text")
            ),
            ui.card(
                ui.output_ui("agent_output_header"),
                # ui.card_header("Agent Output"),
                ui.output_text_verbatim(id="agent_output")
            )
        )
    )
)

agent_running_animation = reactive.Value(False)

def server(input: Inputs, output: Outputs, session: Session):
    @reactive.calc
    def load_data():
        data = df()
        return df()
    
    for measurement in all_measurements:
        value_box_server(measurement, load_data, measurement)


    # Create empty plotly figure on page load
    @render_widget
    def plot():
        fig = go.FigureWidget()
        return fig

    # Update the plotly figure with the latest data
    @reactive.effect
    def _():
        d = load_data()
        with plot.widget.batch_animate():
            fig = plot_timeseries(d)
            plot.widget.update(layout=fig.layout, data=fig.data)

    @render.text
    def logs_text():
        logs_df = logs()
        output = []
        for index, row in logs_df.iterrows():
            wrapped_lines = wrap(f"{row['timestamp']}: {row['message']}", width=64, break_long_words=False)
            output.extend(wrapped_lines)
        return "\n".join(output)
    
    @reactive.effect
    def _():
        d = load_data()
        global agent_running_animation
        global agent_running
        if not agent_running:
            threshold_warning = check_thresholds(d, WARNING_THRESHOLDS)
            if threshold_warning:
                agent_running_animation.set(True)
                run_agent(threshold_warning)

    @render.ui
    def agent_output_header():
        global agent_running_animation
        if agent_running_animation.get():
            print("Agent running, showing animation")
            return ui.card_header(
                ui.tags.div(
                    "Agent Output",
                    ui.tags.span({"class": "loading-dot"}),
                    ui.tags.span({"class": "loading-dot"}),
                    ui.tags.span({"class": "loading-dot"}),
                )
            )
        else:
            return ui.card_header("Agent Output")

    @render.text 
    def agent_output():
        agent_messages = agent_logs()
        output = []
        for index, row in agent_messages.iterrows():
            message_content = row['message'].replace('\n', ' ')
            message = f"{row['time']}: {message_content}"
            wrapped_lines = wrap(message, width=64, break_long_words=False)
            wrapped_lines[-1] += "\n"
            output.extend(wrapped_lines)
        return "\n".join(output)

    @reactive.extended_task
    async def run_agent(warning: str):
        global agent_running
        global agent_running_animation
        agent_running = True
        async for message in invoke_and_stream_agent(warning):
            conn = get_db_connection()
            cur = get_db_cursor(conn)
            insert_agent_message(cur, message)
            conn.commit()
            await asyncio.sleep(0.1)
        agent_running = False
        agent_running_animation.set(False)

    @reactive.effect
    def restart_device():
        if input.restart_device():
            print("Restarting device")
            requests.post("http://127.0.0.1:8000/restart")

    @reactive.effect
    def simulate_failure():
        if input.simulate_failure():
            requests.post("http://127.0.0.1:8000/simulate_failure")

app = App(app_ui, server)