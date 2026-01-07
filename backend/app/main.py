from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json
from datetime import datetime

# ---------------------------------------------------------
# Refactored Imports (Project Structure Update)
# ---------------------------------------------------------
# Imports modified to fit the 'app' directory structure
from app import database
from app.models import models
from app.schemas import schemas

# ---------------------------------------------------------
# Mentor Feedback: Remove create_all
# Use Alembic for migrations in production environments.
# models.Base.metadata.create_all(bind=database.engine) <--- REMOVED
# ---------------------------------------------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"message": "VibeSyncer Backend is connected to Supabase!"}

# Test API: Create User
@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = models.User(username=user.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Test API: Create Room
@app.post("/rooms/", response_model=schemas.RoomResponse)
def create_room(room: schemas.RoomCreate, db: Session = Depends(database.get_db)):
    # Check if user exists
    db_user = db.query(models.User).filter(models.User.id == room.host_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_room = models.Room(name=room.name, host_id=room.host_id)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

@app.post("/rooms/{room_id}/join", response_model=schemas.ParticipantResponse)
def join_room(room_id: int, join_data: schemas.RoomJoin, db: Session = Depends(database.get_db)):
    # 1. Check if room exists
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")

    # 2. Check if user exists
    db_user = db.query(models.User).filter(models.User.id == join_data.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # 3. Check if already joined (Prevent duplicates)
    existing_participant = db.query(models.RoomParticipant).filter(
        models.RoomParticipant.room_id == room_id,
        models.RoomParticipant.user_id == join_data.user_id
    ).first()

    if existing_participant:
        return existing_participant

    # 4. Create participation record
    db_participant = models.RoomParticipant(user_id=join_data.user_id, room_id=room_id)
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

# 1. Get song list for a specific room
@app.get("/rooms/{room_id}/queue_list", response_model=List[schemas.QueueResponse])
def get_room_queue(room_id: int, db: Session = Depends(database.get_db)):
    return db.query(models.QueueItem).filter(models.QueueItem.room_id == room_id).all()

# 2. Add song to a specific room
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
        raise HTTPException(status_code=400, detail="Platform not supported. (Youtube, Soundcloud, Spotify available)")

    db_item = models.QueueItem(
        room_id=room_id,
        user_id=item.user_id,
        title=item.title,
        artist=item.artist,
        music_url=item.music_url,
        platform=detected_platform,
        is_played=False
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # Broadcast "Who added what song" to everyone in the room
    await manager.broadcast_to_room(room_id, {
        "type": "queue_update",
        "user_id": item.user_id,
        "title": db_item.title,
        "music_url": db_item.music_url
    })

    return db_item

# Update song playback status (Host Only)
@app.patch("/rooms/{room_id}/queue/{item_id}", response_model=schemas.QueueResponse)
def update_queue_item(
        room_id: int,
        item_id: int,
        is_played: bool,
        request_user_id: int,
        db: Session = Depends(database.get_db)):

    # 1. Fetch room info
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found.")

    # 2. Authorization: Check if requester is the host
    if db_room.host_id != request_user_id:
        raise HTTPException(status_code=403, detail="Only the host can control the playback/queue.")

    # 3. Find the song item
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
    # 1. Accept connection and register to manager
    await manager.connect(websocket, room_id)

    # Manually get DB session (Depends doesn't work well directly in WebSocket here)
    db_gen = database.get_db()
    db = next(db_gen)

    # Pre-fetch connected user info
    user = db.query(models.User).filter(models.User.id == user_id).first()
    username = user.username if user else f"Unknown({user_id})"

    try:
        while True:
            # 2. Receive message from client (Text format)
            data = await websocket.receive_text()

            # 3. Save chat message to DB
            new_chat = models.ChatMessage(
                room_id=room_id,
                user_id=user_id,
                message=data
            )
            db.add(new_chat)
            db.commit()
            db.refresh(new_chat)

            # 4. Broadcast to all users in the room (JSON format)
            await manager.broadcast_to_room(room_id, {
                "type": "chat",
                "user_id": user_id,
                "username": username,
                "message": data,
                "created_at": new_chat.created_at.isoformat()
            })

    except WebSocketDisconnect:
        # 5. Remove from manager on disconnect
        manager.disconnect(websocket, room_id)
    finally:
        # Close DB session
        db_gen.close()

# Get chat history for a specific room
@app.get("/rooms/{room_id}/chats", response_model=List[schemas.ChatResponse])
def get_room_chats(room_id: int, limit: int = 50, db: Session = Depends(database.get_db)):
    """
    Retrieve recent chat history for a specific room (up to limit).
    """
    chats = db.query(
        models.ChatMessage.id,
        models.ChatMessage.room_id,
        models.ChatMessage.user_id,
        models.ChatMessage.message,
        models.ChatMessage.created_at,
        models.User.username  # Fetch username from User table
        ).join(models.User, models.ChatMessage.user_id == models.User.id) \
         .filter(models.ChatMessage.room_id == room_id) \
         .order_by(models.ChatMessage.created_at.asc()) \
         .limit(limit) \
         .all()
    return chats