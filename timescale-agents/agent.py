from langchain_openai import ChatOpenAI
from langchain.agents import tool, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
import requests
from db import read_log_data, get_db_connection, get_db_cursor
import asyncio

conn = get_db_connection()
cur = get_db_cursor(conn)

llm = ChatOpenAI(model="gpt-4o", temperature=0, streaming=True)
MEMORY_KEY = "agent_memory"
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a powerful hardware-assistant, that monitors the outputs from a sensor device and manages any failures that may arise.
            1. When you are called with an issue, you will try the tools available to you to resolve it, and then verify from the logs if your intervention has resolved the issue or not. 
            2. Always include your thoughts and observations at each step along the way, in a concise, log-like manner
            Example outputs:
            Humidity above warning threshold, attempting to restart device
            Based on logs, restart appears successful.
            Issue seems to persist. Shutting the device down for safety and notify operator.
            """,
        ),
        # MessagesPlaceholder(variable_name=MEMORY_KEY),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


@tool
async def read_log_data_tool():
    """Read the logs to check if the issue is still present"""
    data = read_log_data(cur, 10)
    return data.to_markdown()


@tool
async def restart_device():
    """Restart the device to try and fix issues. Try this up to 2 times before moving on to another tool."""
    requests.post("http://127.0.0.1:8000/restart")
    await asyncio.sleep(3)
    return "Device restarted"


@tool
async def device_failover():
    """Failover to a backup sensor, if the primary sensor continues to fail"""
    requests.post("http://127.0.0.1:8000/failover")
    await asyncio.sleep(3)
    return "Device restarted"


@tool
async def notify_operator():
    """Notify the operator"""
    requests.post("http://127.0.0.1:8000/notify")
    await asyncio.sleep()
    return "Operator notified"


tools = [
    restart_device,
    read_log_data_tool,
    device_failover,
]

llm_with_tools = llm.bind_tools(tools)

agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(
            x["intermediate_steps"]
        ),
    }
    | prompt
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# agent_executor.invoke({"input":"Temperature is too high"})
