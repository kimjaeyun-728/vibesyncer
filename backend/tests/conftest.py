import os
import sys
from pathlib import Path

# Tests must never connect to a developer's database or external AI service.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "backend-regression-tests-only-secret-key"
os.environ["GEMINI_API_KEY"] = ""
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app import database
from app.api.routes import rooms, websockets
from app.core.websocket_manager import manager
from app.models import models


@pytest.fixture
def service(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    models.Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False)
    monkeypatch.setattr(database, "SessionLocal", sessions)

    async def welcome(_):
        return "Welcome!"

    monkeypatch.setattr(websockets, "get_ai_welcome_message", welcome)
    with sessions() as db:
        db.add(models.User(id=0, username="VibeBot"))
        db.commit()

    app = FastAPI()
    app.include_router(rooms.router, prefix="/rooms")
    app.include_router(websockets.router)
    manager.active_connections.clear()
    manager.room_states.clear()
    with TestClient(app) as client:
        yield client, sessions
    manager.active_connections.clear()
    manager.room_states.clear()
    engine.dispose()
