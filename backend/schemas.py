from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# --- 유저(User) ---
class UserBase(BaseModel):
    username: str = Field(..., description="사용자 이름", example="다낭개발자")

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- 방(Room) ---
class RoomBase(BaseModel):
    name: str = Field(..., description="방 제목", example="VibeSyncer 테스트방")

class RoomCreate(RoomBase):
    host_id: int = Field(..., description="호스트 유저 ID")

class RoomResponse(RoomBase):
    id: int
    host_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- 노래 큐(QueueItem) ---
class QueueCreate(BaseModel):
    title: str = Field(..., description="노래 제목", example="Shopper")
    artist: str = Field(..., description="가수", example="IU")
    music_url: str = Field(..., description="음악 URL")
    user_id: int = Field(..., description="추가한 유저 ID")

class QueueResponse(QueueCreate):
    id: int
    room_id: int
    platform: str
    is_played: bool
    created_at: datetime
    class Config:
        from_attributes = True

# --- 채팅(ChatMessage) ---
class ChatResponse(BaseModel):
    id: int
    room_id: int
    user_id: int
    username: str = Field(..., description="보낸 사람 이름") # 이름 연동을 위해 추가
    message: str = Field(..., description="메시지 내용")
    created_at: datetime
    class Config:
        from_attributes = True

# --- 입장(Participant) ---
class RoomJoin(BaseModel):
    user_id: int

class ParticipantResponse(BaseModel):
    id: int
    user_id: int
    room_id: int
    joined_at: datetime
    class Config:
        from_attributes = True