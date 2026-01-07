from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json
import random
import string
from datetime import datetime

# ---------------------------------------------------------
# Imports with 'app' directory structure
# ---------------------------------------------------------
from app import database
from app.models import models
from app.schemas import schemas

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Utility Function: Generate Random Room Code
# ---------------------------------------------------------
def generate_room_code(length=6):
    """Generate a random alphanumeric string of fixed length."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for i in range(length))


# ---------------------------------------------------------
# WebSocket Connection Manager
# ---------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        # Structure: {room_id: [websocket1, websocket2, ...]}
        self.active_connections: dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: int):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        print(f"New connection in room {room_id}. Total: {len(self.active_connections[room_id])}")

    def disconnect(self, websocket: WebSocket, room_id: int):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        print(f"Connection closed in room {room_id}")

    async def broadcast_to_room(self, room_id: int, message: dict):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_json(message)


manager = ConnectionManager()


# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "VibeSyncer Backend is Running!"}


# [Updated] Create Room with Nickname & Auto-generate Room Code
@app.post("/rooms/", response_model=schemas.RoomResponse)
def create_room(room: schemas.RoomCreate, db: Session = Depends(database.get_db)):
    # 1. Handle Host User (Find existing or Create new)
    # Since we don't have login, we treat nickname as identity for now.
    db_user = db.query(models.User).filter(models.User.username == room.host_nickname).first()
    if not db_user:
        db_user = models.User(username=room.host_nickname)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    # 2. Generate Unique Room Code
    # Retry logic in case of collision (very rare with 6 chars)
    while True:
        new_code = generate_room_code()
        existing_code = db.query(models.Room).filter(models.Room.room_code == new_code).first()
        if not existing_code:
            break

    # 3. Create Room
    db_room = models.Room(
        name=room.name,
        host_id=db_user.id,
        room_code=new_code
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)

    return db_room


# [Updated] Join Room using Room Code
@app.post("/rooms/join", response_model=schemas.ParticipantResponse)
def join_room(join_data: schemas.RoomJoin, db: Session = Depends(database.get_db)):
    # 1. Find Room by Room Code (Not ID)
    db_room = db.query(models.Room).filter(models.Room.room_code == join_data.room_code).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Invalid Room Code")

    # 2. Handle User (Find existing or Create new by nickname)
    db_user = db.query(models.User).filter(models.User.username == join_data.nickname).first()
    if not db_user:
        db_user = models.User(username=join_data.nickname)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    # 3. Check if already joined
    existing_participant = db.query(models.RoomParticipant).filter(
        models.RoomParticipant.room_id == db_room.id,
        models.RoomParticipant.user_id == db_user.id
    ).first()

    if existing_participant:
        return existing_participant

    # 4. Create participation record
    db_participant = models.RoomParticipant(user_id=db_user.id, room_id=db_room.id)
    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)

    return db_participant


# Supported Platforms Definition
SUPPORTED_PLATFORMS = {
    "youtube.com": "Youtube",
    "youtu.be": "Youtube",
    "soundcloud.com": "Soundcloud",
    "spotify.com": "Spotify"
}


# ---------------------------------------------------------
# Queue (Music) Related APIs
# ---------------------------------------------------------

@app.get("/rooms/{room_id}/queue_list", response_model=List[schemas.QueueResponse])
def get_room_queue(room_id: int, db: Session = Depends(database.get_db)):
    return db.query(models.QueueItem).filter(models.QueueItem.room_id == room_id).all()


# [Updated] Add song with Thumbnail URL support
@app.post("/rooms/{room_id}/queue", response_model=schemas.QueueResponse)
async def add_to_queue(room_id: int, item: schemas.QueueCreate, db: Session = Depends(database.get_db)):
    # Detect platform via URL analysis
    detected_platform = "Unknown"
    url_lower = item.music_url.lower()
    for domain, name in SUPPORTED_PLATFORMS.items():
        if domain in url_lower:
            detected_platform = name
            break

    if detected_platform == "Unknown":
        raise HTTPException(status_code=400, detail="Platform not supported.")

    db_item = models.QueueItem(
        room_id=room_id,
        user_id=item.user_id,
        title=item.title,
        artist=item.artist,
        music_url=item.music_url,
        thumbnail_url=item.thumbnail_url,  # [New] Save Album Cover
        platform=detected_platform,
        is_played=False
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # Broadcast update
    await manager.broadcast_to_room(room_id, {
        "type": "queue_update",
        "user_id": item.user_id,
        "title": db_item.title,
        "artist": db_item.artist,
        "thumbnail_url": db_item.thumbnail_url,  # [New] Send cover to frontend
        "music_url": db_item.music_url
    })

    return db_item


@app.patch("/rooms/{room_id}/queue/{item_id}", response_model=schemas.QueueResponse)
def update_queue_item(
        room_id: int,
        item_id: int,
        is_played: bool,
        request_user_id: int,
        db: Session = Depends(database.get_db)):
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found.")

    if db_room.host_id != request_user_id:
        raise HTTPException(status_code=403, detail="Only the host can control the playback/queue.")

    db_item = db.query(models.QueueItem) \
        .filter(models.QueueItem.id == item_id, models.QueueItem.room_id == room_id) \
        .first()

    if not db_item:
        raise HTTPException(status_code=404, detail="The song cannot be found.")

    db_item.is_played = is_played
    db.commit()
    db.refresh(db_item)

    return db_item


# ---------------------------------------------------------
# Chat & WebSocket Endpoints
# ---------------------------------------------------------

@app.websocket("/ws/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int, user_id: int):
    await manager.connect(websocket, room_id)

    db_gen = database.get_db()
    db = next(db_gen)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    username = user.username if user else f"Unknown({user_id})"

    try:
        while True:
            data = await websocket.receive_text()

            # [TODO]: Add logic here to detect if 'data' is a URL and add to queue automatically

            new_chat = models.ChatMessage(
                room_id=room_id,
                user_id=user_id,
                message=data
            )
            db.add(new_chat)
            db.commit()
            db.refresh(new_chat)

            await manager.broadcast_to_room(room_id, {
                "type": "chat",
                "user_id": user_id,
                "username": username,
                "message": data,
                "created_at": new_chat.created_at.isoformat()
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
    finally:
        db_gen.close()


@app.get("/rooms/{room_id}/chats", response_model=List[schemas.ChatResponse])
def get_room_chats(room_id: int, limit: int = 50, db: Session = Depends(database.get_db)):
    chats = db.query(
        models.ChatMessage.id,
        models.ChatMessage.room_id,
        models.ChatMessage.user_id,
        models.ChatMessage.message,
        models.ChatMessage.created_at,
        models.User.username
    ).join(models.User, models.ChatMessage.user_id == models.User.id) \
        .filter(models.ChatMessage.room_id == room_id) \
        .order_by(models.ChatMessage.created_at.asc()) \
        .limit(limit) \
        .all()
    return chats