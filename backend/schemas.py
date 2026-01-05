from pydantic import BaseModel
from datetime import datetime

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