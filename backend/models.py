from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

# 1. 사용자(User) 테이블
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정 (유저가 만든 방들)
    rooms = relationship("Room", back_populates="host")

# 2. 방(Room) 테이블
class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    host_id = Column(Integer, ForeignKey("users.id")) # 방장(User)의 ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정 (방의 주인)
    host = relationship("User", back_populates="rooms")
    participants = relationship("RoomParticipant", back_populates="room")

class RoomParticipant(Base):
    __tablename__ = "room_participants"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    #관계 설정
    user = relationship("User")
    room = relationship("Room", back_populates="participants")

# 채팅 메시지(Chat) 테이블
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id  = Column(Integer, ForeignKey("rooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정
    user = relationship("User")
    room = relationship("Room")

class QueueItem(Base):
    __tablename__ = "queue_items"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    artist = Column(String)
    music_url = Column(String)
    platform = Column(String)
    is_played = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    room = relationship("Room")
    user = relationship("User")