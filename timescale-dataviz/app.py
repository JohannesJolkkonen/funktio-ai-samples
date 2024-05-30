import instructor
from decouple import config
from openai import AsyncOpenAI
from string import Template
from pydantic import BaseModel
from enum import Enum
from typing import List
import streamlit as st
from visualization import get_bar_chart, get_pie_chart, get_forecast_chart
from typing import List
from pydantic import BaseModel, Field
from enum import Enum
from db import get_db_connection, get_db_cursor, get_table_info
import psycopg2
import asyncio
from timeit import default_timer as timer

async_client = instructor.patch(AsyncOpenAI(api_key=config("OPENAI_API_KEY")))

st.set_page_config(layout="wide")


@st.cache_resource
def init_db():
    conn = get_db_connection()
    cur = get_db_cursor(conn)
    return cur, conn


cur, conn = init_db()

analysis_system_message = """
You are a PostgreSQL and data visualization expert. Given a data visualization request, you return a visualization plan consisting of visualization tasks.
Each visualization task consists of:
1. Syntactically correct PostgreSQL query to get the data necessary to answer the request.
2. The correct visualization type to use (BAR_CHART or PIE_CHART or FORECAST), with the required parameters. 
3. Parameters for the task, as a dictionary:
    - Pie chart tasks require no parameters
    - Bar chart tasks require a 'bar_mode', either "group" or "stack".
    - Forecast tasks require a 'n_days' for number of days to forecast, and 'prediction_model', either "arima" or "exponential".

Example parameters:
    - bar chart: {"bar_mode": "group"}
    - forecast: {"n_days": 20, "prediction_model": "arima"}

You will never return a visualization task with empty parameters.
    
For forecasting tasks, never combine multiple values or cryptos in one query. 

When generating the PostgreSQL queries, follow the instructions below:
- Remember to aggregate when possible to return only the necessary number of rows.
- Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.
- Pay attention to use only the column names you can see in the table given below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
- If the question involves "today", remember to use the CURRENT_DATE function.
- Always include the "symbol" column in the query.
- Always use the alias "value" for the numerical value in the query, whether it's a price or volume.
- Write the PostgreSQL query without formatting it in a code block.

Think step by step before writing the query plan.
"""

request_prompt_template = Template(
"""
Request: $input

Use the following tables:
$table_info

"""
)

async def async_generate_visualization_plan(table_info, question):
    placeholder = st.empty()
    plan = await async_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": analysis_system_message},
            {
                "role": "user",
                "content": request_prompt_template.substitute(
                    input=question, table_info=table_info
                ),
            },
        ],
        stream=True,
        response_model=instructor.Partial[VisualizationPlan],
    )
    result = None
    async for obj in plan:
        placeholder.empty()
        placeholder.write(obj.model_dump())
        result = obj

    placeholder.empty()
    return result


class VisualizationType(Enum):
    BAR_CHART = "BAR_CHART"
    PIE_CHART = "PIE_CHART"
    FORECAST = "FORECAST"


class VisualizationTask(BaseModel):
    query: str = Field(
        ..., description="PostgreSQL-query to fetch data for visualization"
    )
    type: VisualizationType
    title: str = Field(..., description="Title of the visualization")
    parameters: dict = Field(
        ..., description="Parameters for the visualization task, as a dictionary"
    )

    def _execute_query(self):
        try:
            cur.execute(self.query)
        except psycopg2.Error as e:
            print(f"An error occurred: {e}")
            conn.rollback()  # Rollback the transaction on error
        return cur.fetchall()

    def run(self):
        data = self._execute_query()
        print(data)
        if self.type == VisualizationType.BAR_CHART:
            fig = get_bar_chart(
                data=data, title=self.title, barmode=self.parameters.get("bar_mode")
            )
            return fig

        elif self.type == VisualizationType.PIE_CHART:
            fig = get_pie_chart(data=data, title=self.title)
            return fig

        elif self.type == VisualizationType.FORECAST: 
            cols = [desc[0] for desc in cur.description]
            fig = get_forecast_chart(
                data=data,
                cols=cols,
                title=self.title,
                n_days=self.parameters.get("n_days"),
                model=self.parameters.get("prediction_model"),
            )
            return fig


class VisualizationPlan(BaseModel):
    plan: List[VisualizationTask]

    def run(self):
        num_tasks = len(self.plan)
        num_rows = (num_tasks + 1) // 2
        for row in range(num_rows):
            st_cols = st.columns(2)
            for col in range(2):
                task_index = row * 2 + col
                if task_index < num_tasks:
                    with st_cols[col]:
                        fig = self.plan[task_index].run()
                        st.plotly_chart(fig)


## Streamlit UI

if 'user_input' not in st.session_state:
    st.session_state.user_input = ""

st.title("Crypto Data Visualizer 📊📈")

def set_user_input(question):
    st.session_state.user_input = question

def set_user_input_from_field():
    st.session_state.user_input = st.session_state.input_field_value

input_field = st.text_input("Enter a question", value=st.session_state.get("user_input"), key="input_field_value", on_change=set_user_input_from_field)

example_questions = ["Price of BTC in the last 30D", "Daily volumes for ETH and BTC in March 2024", "Forecast SOL prices for next 7 days, based on last 14 days"]
button_cols = st.columns([0.6, 1, 1, 2, 2])

for i, question in enumerate(example_questions):
    with button_cols[i]:
        st.button(question, on_click=set_user_input, args=(question,))

if len(st.session_state.user_input) > 0:
    user_input = st.session_state.user_input
    with st.spinner("Generating query plan..."):
        start = timer()
        visualization_plan = asyncio.run(
            async_generate_visualization_plan(
                get_table_info(cur, "crypto_data"), user_input
            )
        )
        end = timer()
        st.info(f"Query plan generated in {round(end - start, 2)} seconds")
        print(visualization_plan.model_dump())
    st.write(visualization_plan.model_dump())
    visualization_plan.run()
