from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
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