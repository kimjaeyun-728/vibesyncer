# app/schemas/schemas.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# --- User Schemas ---
class UserBase(BaseModel):
    # Description updated for better API docs
    username: str = Field(..., description="User's nickname", example="VibeMaster")

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- Room Schemas ---
class RoomBase(BaseModel):
    name: str = Field(..., description="Title of the room", example="K-Pop Party")

class RoomCreate(RoomBase):
    # Now we need host's nickname instead of ID to support "One-Step Creation"
    host_nickname: str = Field(..., description="Nickname of the host creating the room")

class RoomResponse(RoomBase):
    id: int
    room_code: str = Field(..., description="Unique 6-character code for invitation")
    host_id: int

    host_nickname: str = Field(..., description="Nickname of the host")
    created_at: datetime
    class Config:
        from_attributes = True

# --- Queue Item Schemas ---
class QueueCreate(BaseModel):
    title: str = Field(..., description="Song title", example="Shopper")
    artist: str = Field(..., description="Artist name", example="IU")
    music_url: str = Field(..., description="URL of the music")
    thumbnail_url: Optional[str] = Field(None, description="URL of the album cover")
    user_id: int = Field(..., description="ID of the user who added the song")

class QueueResponse(QueueCreate):
    id: int
    room_id: int
    platform: str
    is_played: bool
    created_at: datetime
    class Config:
        from_attributes = True

# --- Chat Schemas ---
class ChatResponse(BaseModel):
    id: int
    room_id: int
    user_id: int
    username: str = Field(..., description="Sender's username")
    message: str = Field(..., description="Chat message content")
    created_at: datetime
    class Config:
        from_attributes = True

# --- Participant Schemas ---
class RoomJoin(BaseModel):
    # Join by Room Code + Nickname
    room_code: str = Field(..., description="Room code to join")
    nickname: str = Field(..., description="User's nickname")

class ParticipantResponse(BaseModel):
    id: int
    user_id: int
    room_id: int

    room_name: str = Field(..., description="Name of the joined room")
    room_code: str = Field(..., description="Code of the joined room")
    host_nickname: str = Field(..., description="Nickname of the room host")
    nickname: str = Field(..., description="Nickname of the joining user")

    joined_at: datetime
    class Config:
        from_attributes = True

class RoomHostResponse(BaseModel):
    room_code: str = Field(..., description="Room code queried")
    host_nickname: str = Field(..., description="Nickname of the host")

    class Config:
        from_attributes = True