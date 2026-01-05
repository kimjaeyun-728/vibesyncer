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