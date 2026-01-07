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

    def disconnect(self, websocket: WebSocket, room_id: int):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast_to_room(self, room_id: int, message: dict):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Handle disconnected sockets gracefully
                    pass


manager = ConnectionManager()


# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "VibeSyncer Backend is Running!"}


# [Updated] Create Room: Create a new user unconditionally
@app.post("/rooms/", response_model=schemas.RoomResponse)
def create_room(room: schemas.RoomCreate, db: Session = Depends(database.get_db)):
    # 1. Always create a new host user (Allow duplicates globally)
    # Since we removed the unique constraint on username, this is now valid.
    db_user = models.User(username=room.host_nickname)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # 2. Generate Unique Room Code
    # Retry logic to ensure the code is unique
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


# [Updated] Join Room: Check nickname duplication within the specific room
@app.post("/rooms/join", response_model=schemas.ParticipantResponse)
def join_room(join_data: schemas.RoomJoin, db: Session = Depends(database.get_db)):
    # 1. Find Room by Room Code
    db_room = db.query(models.Room).filter(models.Room.room_code == join_data.room_code).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Invalid Room Code")

    # 2. [New] Check if nickname already exists in this specific room
    # We join RoomParticipant and User tables to check the current participants.
    duplicate_user = db.query(models.RoomParticipant) \
        .join(models.User) \
        .filter(models.RoomParticipant.room_id == db_room.id) \
        .filter(models.User.username == join_data.nickname) \
        .first()

    if duplicate_user:
        raise HTTPException(status_code=409, detail="Nickname already exists in this room.")

    # 3. Create a new user (Specific to this room session)
    db_user = models.User(username=join_data.nickname)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # 4. Add to participant list
    db_participant = models.RoomParticipant(user_id=db_user.id, room_id=db_room.id)
    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)

    return db_participant


# [New] Leave Room (Guest)
@app.post("/rooms/leave")
async def leave_room(room_id: int, user_id: int, db: Session = Depends(database.get_db)):
    # 1. Verify participant existence
    participant = db.query(models.RoomParticipant).filter(
        models.RoomParticipant.room_id == room_id,
        models.RoomParticipant.user_id == user_id
    ).first()

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    # 2. Get user info for notification
    user = db.query(models.User).filter(models.User.id == user_id).first()
    username = user.username if user else "Unknown"

    # 3. Delete data (Participant -> User)
    db.delete(participant)
    if user:
        db.delete(user)  # Delete the session-based user
    db.commit()

    # 4. Notify remaining users
    await manager.broadcast_to_room(room_id, {
        "type": "system",
        "message": f"{username} has left the room."
    })

    return {"message": "Successfully left the room"}


# [New] Dissolve Room (Host)
@app.delete("/rooms/{room_code}")
async def delete_room(room_code: str, request_user_id: int, db: Session = Depends(database.get_db)):
    # 1. Find Room
    db_room = db.query(models.Room).filter(models.Room.room_code == room_code).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")

    # 2. Verify permission (Host only)
    if db_room.host_id != request_user_id:
        raise HTTPException(status_code=403, detail="Only the host can dissolve the room")

    room_id = db_room.id

    # 3. Collect user IDs to delete (Host + All participants)
    # Since the room is being deleted, all session users attached to it should be removed.
    users_to_delete = [db_room.host_id]
    participants = db.query(models.RoomParticipant).filter(models.RoomParticipant.room_id == room_id).all()
    for p in participants:
        users_to_delete.append(p.user_id)

    # 4. Delete related data (Cascade manually)
    # 4-1. Delete Queue Items
    db.query(models.QueueItem).filter(models.QueueItem.room_id == room_id).delete()
    # 4-2. Delete Chat Messages
    db.query(models.ChatMessage).filter(models.ChatMessage.room_id == room_id).delete()
    # 4-3. Delete Participants
    db.query(models.RoomParticipant).filter(models.RoomParticipant.room_id == room_id).delete()

    # 5. Delete Room
    db.delete(db_room)

    # 6. Delete User Data
    # (Use set to remove duplicates before deletion)
    for uid in set(users_to_delete):
        u = db.query(models.User).filter(models.User.id == uid).first()
        if u:
            db.delete(u)

    db.commit()

    # 7. Broadcast 'Room Deleted' notification (Client should handle redirect)
    await manager.broadcast_to_room(room_id, {
        "type": "room_deleted",
        "message": "The host has dissolved the room."
    })

    return {"message": "Room deleted successfully"}


# --- Existing APIs (Queue, Chat, etc.) ---
SUPPORTED_PLATFORMS = {
    "youtube.com": "Youtube",
    "youtu.be": "Youtube",
    "soundcloud.com": "Soundcloud",
    "spotify.com": "Spotify"
}


@app.get("/rooms/{room_id}/queue_list", response_model=List[schemas.QueueResponse])
def get_room_queue(room_id: int, db: Session = Depends(database.get_db)):
    return db.query(models.QueueItem).filter(models.QueueItem.room_id == room_id).all()


@app.post("/rooms/{room_id}/queue", response_model=schemas.QueueResponse)
async def add_to_queue(room_id: int, item: schemas.QueueCreate, db: Session = Depends(database.get_db)):
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
        thumbnail_url=item.thumbnail_url,
        platform=detected_platform,
        is_played=False
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    await manager.broadcast_to_room(room_id, {
        "type": "queue_update",
        "user_id": item.user_id,
        "title": db_item.title,
        "artist": db_item.artist,
        "thumbnail_url": db_item.thumbnail_url,
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