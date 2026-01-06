from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# --- User 스키마 ---
class UserCreate(BaseModel):
    username: str

class UserResponse(UserCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- Room 스키마 ---
class RoomCreate(BaseModel):
    name: str
    host_id: int

class RoomResponse(RoomCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class RoomJoin(BaseModel):
    user_id: int

class ParticipantResponse(BaseModel):
    id: int
    user_id: int
    room_id: int
    joined_at: datetime

    class Config:
        from_attributes = True

# Chat 스키마
class ChatCreate(BaseModel):
    message: str
    user_id: int

class ChatResponse(ChatCreate):
    id: int
    room_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Queue 스키마
class QueueCreate(BaseModel):
    title: str
    artist: str
    music_url: str
    platform: str
    user_id: int

class QueueResponse(QueueCreate):
    id: int
    room_id: int
    is_played: bool
    created_at: datetime
    class Config:
        from_attributes = True