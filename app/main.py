import asyncio
import socketio
from contextlib import asynccontextmanager
from pathlib import Path
from app.middlewares.cors import configure_cors
from app.middlewares.log import log_requests
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from app.routers import auth
from app.services.socket import sio, redis_listener


def run_migrations() -> None:
    project_root = Path(__file__).resolve().parents[1]
    alembic_config = Config(str(project_root / "alembic.ini"))
    command.upgrade(alembic_config, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    listener_task = asyncio.create_task(redis_listener())
    try:
        yield
    finally:
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan, debug=True)

app.middleware("http")(log_requests)
configure_cors(app)


app.include_router(auth.router)

socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

app = socket_app
