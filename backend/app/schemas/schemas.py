from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# --- User Schemas ---
class UserBase(BaseModel):
    username: str = Field(..., description="Username", example="DanangDeveloper")

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- Room Schemas ---
class RoomBase(BaseModel):
    name: str = Field(..., description="Title of the room", example="VibeSyncer Test Room")

class RoomCreate(RoomBase):
    host_id: int = Field(..., description="ID of the host user")

class RoomResponse(RoomBase):
    id: int
    host_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- Queue Item Schemas ---
class QueueCreate(BaseModel):
    title: str = Field(..., description="Song title", example="Shopper")
    artist: str = Field(..., description="Artist name", example="IU")
    music_url: str = Field(..., description="URL of the music")
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
    username: str = Field(..., description="Sender's username") # Added for frontend display
    message: str = Field(..., description="Chat message content")
    created_at: datetime
    class Config:
        from_attributes = True

# --- Participant Schemas ---
class RoomJoin(BaseModel):
    user_id: int

class ParticipantResponse(BaseModel):
    id: int
    user_id: int
    room_id: int
    joined_at: datetime
    class Config:
        from_attributes = True