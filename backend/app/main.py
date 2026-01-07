import logging
import random
import string
from typing import List, Optional
import re
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

# Imports with 'app' directory structure
from app import database
from app.models import models
from app.schemas import schemas
from app.utils import extract_video_metadata, detect_platform

# [Fix] Add API Metadata
app = FastAPI(
    title="VibeSyncer API",
    description="Real-time collaborative music platform with WebSocket support",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# [Fix] Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------
def generate_room_code(length=6):
    """Generate a random alphanumeric string of fixed length."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for i in range(length))


# [Moved Up] Common logic to add music to DB (Used by both API and WebSocket)
async def process_music_addition(
        room_id: int,
        user_id: int,
        music_url: str,
        db: Session,
        thumbnail_url: Optional[str] = None,
        title: str = "Unknown Title",
        artist: str = "Unknown Artist"
):
    # 1. Detect Platform (Using utility function)
    detected_platform = detect_platform(music_url)

    if not detected_platform:
        return None  # Return None if platform is not supported

    # 2. Extract Real Metadata
    # [Updated] Now supports Youtube, Soundcloud, and Spotify
    TARGET_PLATFORMS = ["Youtube", "Soundcloud", "Spotify"]

    if detected_platform in TARGET_PLATFORMS:
        # Attempt extraction only if title is placeholder
        if title == "Unknown Title" or title.startswith("Shared by"):
            metadata = extract_video_metadata(music_url)
            if metadata:
                title = metadata.get("title", title)
                artist = metadata.get("artist", artist)

                if not thumbnail_url:
                    thumbnail_url = metadata.get("thumbnail_url")

    # 3. Save to DB
    db_item = models.QueueItem(
        room_id=room_id,
        user_id=user_id,
        title=title,
        artist=artist,
        music_url=music_url,
        thumbnail_url=thumbnail_url,
        platform=detected_platform,
        is_played=False
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item


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
                except Exception as e:
                    # [Fix] Log the exception instead of silent pass
                    logger.error(f"Failed to send message to connection: {e}")
                    pass


manager = ConnectionManager()


# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "VibeSyncer Backend is Running!"}


@app.post("/rooms/", response_model=schemas.RoomResponse)
def create_room(room: schemas.RoomCreate, db: Session = Depends(database.get_db)):
    # 1. Create Host User
    db_user = models.User(username=room.host_nickname)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # 2. Generate Code
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


@app.post("/rooms/join", response_model=schemas.ParticipantResponse)
def join_room(join_data: schemas.RoomJoin, db: Session = Depends(database.get_db)):
    db_room = db.query(models.Room).filter(models.Room.room_code == join_data.room_code).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Invalid Room Code")

    duplicate_user = db.query(models.RoomParticipant) \
        .join(models.User) \
        .filter(models.RoomParticipant.room_id == db_room.id) \
        .filter(models.User.username == join_data.nickname) \
        .first()

    if duplicate_user:
        raise HTTPException(status_code=409, detail="Nickname already exists in this room.")

    db_user = models.User(username=join_data.nickname)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    db_participant = models.RoomParticipant(user_id=db_user.id, room_id=db_room.id)
    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)

    return db_participant


@app.post("/rooms/leave")
async def leave_room(room_id: int, user_id: int, db: Session = Depends(database.get_db)):
    participant = db.query(models.RoomParticipant).filter(
        models.RoomParticipant.room_id == room_id,
        models.RoomParticipant.user_id == user_id
    ).first()

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    username = user.username if user else "Unknown"

    db.delete(participant)
    if user:
        db.delete(user)
    db.commit()

    await manager.broadcast_to_room(room_id, {
        "type": "system",
        "message": f"{username} has left the room."
    })

    return {"message": "Successfully left the room"}


@app.delete("/rooms/{room_code}")
async def delete_room(room_code: str, request_user_id: int, db: Session = Depends(database.get_db)):
    db_room = db.query(models.Room).filter(models.Room.room_code == room_code).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")

    if db_room.host_id != request_user_id:
        raise HTTPException(status_code=403, detail="Only the host can dissolve the room")

    room_id = db_room.id

    # [Fix] Removed manual deletion logic.
    # Database ON DELETE CASCADE will handle cleanup for queue, chats, and participants.

    # Delete Room
    db.delete(db_room)

    # Delete Host User
    host_user = db.query(models.User).filter(models.User.id == request_user_id).first()
    if host_user:
        db.delete(host_user)

    db.commit()

    await manager.broadcast_to_room(room_id, {
        "type": "room_deleted",
        "message": "The host has dissolved the room."
    })

    return {"message": "Room deleted successfully"}


# --- Queue & Chat APIs ---

@app.get("/rooms/{room_id}/queue_list", response_model=List[schemas.QueueResponse])
def get_room_queue(room_id: int, db: Session = Depends(database.get_db)):
    return db.query(models.QueueItem).filter(models.QueueItem.room_id == room_id).all()


@app.post("/rooms/{room_id}/queue", response_model=schemas.QueueResponse)
async def add_to_queue(room_id: int, item: schemas.QueueCreate, db: Session = Depends(database.get_db)):
    # [Refactored] Use 'process_music_addition' to reuse logic
    db_item = await process_music_addition(
        room_id=room_id,
        user_id=item.user_id,
        music_url=item.music_url,
        db=db,
        thumbnail_url=item.thumbnail_url,  # Frontend might provide this
        title=item.title,  # Frontend might provide this
        artist=item.artist  # Frontend might provide this
    )

    # If detection failed (process_music_addition returns None)
    if not db_item:
        raise HTTPException(status_code=400, detail="Platform not supported")

    # Broadcast update to all users in the room
    await manager.broadcast_to_room(room_id, {
        "type": "queue_update",
        "user_id": item.user_id,
        "title": db_item.title,
        "artist": db_item.artist,
        "thumbnail_url": db_item.thumbnail_url,
        "music_url": db_item.music_url
    })

    return db_item
    # [Fix] Removed unreachable 'db.add/commit' lines here


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

    # [Fix] Restored URL detection Regex
    url_pattern = re.compile(r'(https?://\S+)')

    try:
        while True:
            data = await websocket.receive_text()

            # 1. Save Chat Message
            new_chat = models.ChatMessage(
                room_id=room_id,
                user_id=user_id,
                message=data
            )
            db.add(new_chat)
            db.commit()
            db.refresh(new_chat)

            # 2. Broadcast Chat Message
            await manager.broadcast_to_room(room_id, {
                "type": "chat",
                "user_id": user_id,
                "username": username,
                "message": data,
                "created_at": new_chat.created_at.isoformat()
            })

            # 3. [Fix] Restored URL Auto-Detection Logic
            found_urls = url_pattern.findall(data)
            for url in found_urls:
                # Try to add to queue using shared logic
                added_item = await process_music_addition(
                    room_id=room_id,
                    user_id=user_id,
                    music_url=url,
                    db=db,
                    title=f"Shared by {username}",  # Temporary Title (Crawler will update this)
                    artist="Unknown"
                )

                # If successfully added (Valid Platform)
                if added_item:
                    # Notify everyone that a song was auto-added
                    await manager.broadcast_to_room(room_id, {
                        "type": "queue_update",
                        "user_id": user_id,
                        "title": added_item.title,
                        "artist": added_item.artist,
                        "thumbnail_url": added_item.thumbnail_url,
                        "music_url": added_item.music_url
                    })

                    # Optional: Send system message
                    await manager.broadcast_to_room(room_id, {
                        "type": "system",
                        "message": f"🎵 '{added_item.title}' has been added to the queue!"
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