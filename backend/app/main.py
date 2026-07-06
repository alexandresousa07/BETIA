import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config.settings import get_settings
from app.core.exceptions import AppException, app_exception_handler, generic_exception_handler
from app.services.cache import cache_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await cache_service.connect()
    yield
    await cache_service.disconnect()


app = FastAPI(
    title=settings.app_name,
    description="Plataforma de IA para análise de partidas de futebol em tempo real",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
app.include_router(api_router)


class ConnectionManager:
    def __init__(self):
        self.active: dict[int, list[WebSocket]] = {}

    async def connect(self, match_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active.setdefault(match_id, []).append(websocket)

    def disconnect(self, match_id: int, websocket: WebSocket):
        if match_id in self.active:
            self.active[match_id] = [ws for ws in self.active[match_id] if ws != websocket]

    async def broadcast(self, match_id: int, message: dict):
        for ws in self.active.get(match_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@app.websocket("/ws/match/{match_id}")
async def match_websocket(websocket: WebSocket, match_id: int):
    await manager.connect(match_id, websocket)
    pubsub = cache_service._redis.pubsub() if cache_service._redis else None
    try:
        if pubsub:
            await pubsub.subscribe(f"match:{match_id}")

        await websocket.send_json({"type": "connected", "match_id": match_id})

        while True:
            if pubsub:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("data"):
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
            else:
                await asyncio.sleep(1)
                await websocket.send_json({"type": "heartbeat"})
    except WebSocketDisconnect:
        manager.disconnect(match_id, websocket)
    finally:
        if pubsub:
            await pubsub.unsubscribe(f"match:{match_id}")
            await pubsub.close()
