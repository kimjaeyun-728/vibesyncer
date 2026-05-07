from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


# 1. User Table
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship: Rooms created by the user
    rooms = relationship("Room", back_populates="host")


# 2. Room Table
class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    room_code = Column(String, unique=True, index=True, nullable=True)

    # Host of the room
    host_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    host = relationship("User", back_populates="rooms")
    participants = relationship("RoomParticipant", back_populates="room")

    @property
    def host_nickname(self):
        return self.host.username if self.host else "Unknown"


# Room Participant Table
class RoomParticipant(Base):
    __tablename__ = "room_participants"

    id = Column(Integer, primary_key=True, index=True)
    # Cascade delete: Remove participant if User or Room is deleted
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"))
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    room = relationship("Room", back_populates="participants")


# Chat Message Table
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    # Cascade delete: Remove messages if Room or User is deleted
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    message = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    room = relationship("Room")


# Music Queue Item Table
class QueueItem(Base):
    __tablename__ = "queue_items"

    id = Column(Integer, primary_key=True, index=True)
    # Cascade delete: Remove songs if Room or User is deleted
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String)
    artist = Column(String)
    thumbnail_url = Column(String, nullable=True)
    music_url = Column(String)
    platform = Column(String)
    is_played = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    room = relationship("Room")
    user = relationship("User")