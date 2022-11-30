import asyncio
import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List
import traceback
import aioredis
from aioredis.client import Redis, PubSub
from fastapi import FastAPI, WebSocket,Request
from chatServer import ChatServer


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



app = FastAPI()


# @app.middleware("http")
# async def add_process_time_header(request: Request, call_next):
#     if request.method =="OPTIONS":
#         headers = {}
#         headers["Content-Type"] = "application/json"
#         headers["Accept"] = "application/json"
#         headers["Access-Control-Allow-Origin"] = "*"
#         headers["Access-Control-Allow-Methods"] = "POST, GET, PUT, DELETE"
#         headers["Access-Control-Allow-Headers"] = "*"
#         headers["X-Frame-Options"] = "SAMEORIGIN"


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message, mode="text")


manager = ConnectionManager()



@app.websocket("/ws/{channel_id}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, channel_id: str, client_id: str):
    try:
        await manager.connect(websocket)
        chat_server = ChatServer(websocket, channel_id, client_id)
        await chat_server.run()
    except:
        print(traceback.format_exc())