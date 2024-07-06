from fastapi import FastAPI
from db import (
    get_db_cursor,
    get_db_connection,
    SensorData,
    insert_sensor_data,
    insert_log_data,
    create_tables,
)
import numpy as np
from datetime import datetime
import asyncio
import random


app = FastAPI()

conn = get_db_connection()
cur = get_db_cursor(conn)
temp_multiplier = 1


class Device:
    def __init__(self, id):
        self.id = id
        self.sensor_running = True
        self.temp_multiplier = 1
        self.overheating = False
        self.connectivity_issues = False
        self.sensor_interval = 0.8

    async def start(self):
        self.sensor_running = False
        insert_log_data(cur, f"Starting device {self.id}")
        conn.commit()
        self.temp_multiplier = 1
        if np.random.randint(0, 3) == 1:
            self.overheating = False
        await asyncio.sleep(2.5)
        insert_log_data(cur, f"Device {self.id} restarted")
        self.sensor_running = True
        asyncio.create_task(self.stream_sensor_data())
        conn.commit()
        await asyncio.sleep(1)

    async def overheat(self):
        while self.overheating:
            self.temp_multiplier += 0.1
            await asyncio.sleep(1.5)

    def simulate_failure(self):
        failure_types = ["Overheating"]  # , "Connectivity issue"]
        failure = random.choice(failure_types)
        print(f"Simulated failure: {failure}")
        if failure == "Overheating":
            self.overheating = True
            asyncio.create_task(self.overheat())

    async def stream_sensor_data(self):
        while self.sensor_running:
            temperature = round(np.random.randint(25, 30) * self.temp_multiplier, 1)
            humidity = np.random.randint(17, 22)
            sensor_data = SensorData(
                sensor_id=str(self.id),
                timestamp=datetime.now(),
                temperature=temperature,
                humidity=humidity,
            )
            insert_sensor_data(cur, sensor_data)
            attributes = {
                k: v for k, v in sensor_data.model_dump().items() if k != "timestamp"
            }
            insert_log_data(cur, f"Data transmission successful:\n{attributes}")
            conn.commit()
            if temperature >= 40:
                pass
            await asyncio.sleep(self.sensor_interval)


@app.post("/restart")
async def restart_device():
    asyncio.create_task(device.start())
    return


@app.post("/simulate_failure")
async def simulate_failure():
    device.simulate_failure()
    return


@app.post("/failover")
async def failover():
    global device
    device.sensor_running = False
    new_id = int(device.id) + 1
    insert_log_data(cur, f"Device {device.id} failed over to device {new_id}")
    conn.commit()
    device = Device(id=new_id)
    asyncio.create_task(device.start())
    return


create_tables(cur)
device = Device(id="1")
conn.commit()
