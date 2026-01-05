from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, database

# 1. 서버가 켜질 때 Supabase에 테이블을 자동으로 만듭니다 (가장 중요!)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()


# 2. 테스트용 API: 사용자 만들기 (POST)
@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = models.User(username=user.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# 3. 테스트용 API: 방 만들기 (POST)
@app.post("/rooms/", response_model=schemas.RoomResponse)
def create_room(room: schemas.RoomCreate, db: Session = Depends(database.get_db)):
    # 존재하는 유저인지 확인
    db_user = db.query(models.User).filter(models.User.id == room.host_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_room = models.Room(name=room.name, host_id=room.host_id)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room


@app.get("/")
def read_root():
    return {"message": "VibeSyncer Backend is connected to Supabase!"}

@app.post("/rooms/{room_id}/join", response_model=schemas.ParticipantResponse)
def join_room(room_id: int, join_data: schemas.RoomJoin, db: Session = Depends(database.get_db)):
    #1. 방이 존재하는지 확인
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")

    #2. 유저가 존재하는지 확인
    db_user = db.query(models.User).filter(models.User.id == join_data.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    #3. 이미 입장해 있는지 확인 (중복 입장 방지)
    existing_participant = db.query(models.RoomParticipant).filter(
        models.RoomParticipant.room_id == room_id,
        models.RoomParticipant.user_id == join_data.user_id
    ).first()

    if existing_participant:
        return existing_participant

    # 4. 입장 기록 생성
    db_participant = models.RoomParticipant(user_id=join_data.user_id, room_id=room_id)
    db.add(db_participant)
    db.commit()
    db.refresh(db_participant)
    return db_participant