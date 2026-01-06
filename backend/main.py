from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, database
from typing import List
from fastapi import HTTPException, WebSocket, WebSocketDisconnect
from database import get_db
from fastapi import Body

# 1. 서버가 켜질 때 Supabase에 테이블을 자동으로 만듭니다 (가장 중요!)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        #{room_id: [websocket1, websocket2, ...]} 구조
        self.active_connections: dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: int):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        print(f"New connection in room {room_id}. Total: {len(self.active_connections[room_id])}")

    def disconnect(self, websocket: WebSocket, room_id: int):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        print(f"Connection closed in room {room_id}")

    async def broadcast_to_room(self, room_id: int, message: dict):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_json(message)

manager = ConnectionManager()

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

# 지원 플랫폼 정의
SUPPORTED_PLATFORMS = {
    "youtube.com": "Youtube",
    "youtu.be": "Youtube",
    "soundcloud.com": "Soundcloud",
    "spotify.com": "Spotify"
}

# 노래 큐(Queue) 관련 API

# 1. 특정 방의 노래 목록 조회
@app.get("/rooms/{room_id}", response_model=List[schemas.RoomResponse])
def get_room_queue(room_id: str, db: Session = Depends(database.get_db)):
    return db.query(models.QueueItem).filter(models.QueueItem.room_id == room_id).all()

# 2. 특정 방에 노래 추가
@app.post("/rooms/{room_id}/queue", response_model=schemas.QueueResponse)
async def add_to_queue(room_id: int, item: schemas.QueueCreate, db: Session = Depends(database.get_db)):
    # URL 분석을 통한 플랫폼 판별
    detected_platform = "Unknown"
    url_lower = item.music_url.lower()
    for domain, name in SUPPORTED_PLATFORMS.items():
        if domain in url_lower:
            detected_platform = name
            break

    if detected_platform == "Unknown":
        raise HTTPException(status_code=404, detail="Platform not supported. (Youtube, Soundcloud, Spotify available)")

    db_item = models.QueueItem(
        room_id=room_id,
        user_id=item.user_id,
        title=item.title,
        artist=item.artist,
        music_url=item.music_url,
        platform=detected_platform,
        is_played=False
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # 같은 방 사람들에게 "누가 무슨 노래를 추가 했는지" 알람 전송
    await manager.broadcast_to_room(room_id, {
        "type": "queue_update",
        "user_id": item.user_id,
        "title": db_item.title,
        "music_url": db_item.music_url
    })


    return db_item

@app.websocket("/ws/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int, user_id: int):
    # 1. 연결 수락 및 관리자에 등록
    await manager.connect(websocket,room_id)

    # DB 세션을 수동으로 가져오기 위한 설정
    db_gen = get_db()
    db = next(db_gen)

    try:
        while True:
            # 2. 클라이언트로부터 메시지 수신 (텍스트 형태)
            data = await websocket.receive_text()

            # 3. DB에 채팅 내용 저장
            new_chat = models.ChatMessage(
                room_id=room_id,
                user_id=user_id,
                message=data
            )
            db.add(new_chat)
            db.commit()
            db.refresh(new_chat)

            # 4. 같은 방에 있는 모든 사람에게 브로드캐스트 (JSON 형식)
            await manager.broadcast_to_room(room_id, {
                "type": "chat",
                "user_id": user_id,
                "username": f"User{user_id}",
                "message": data,
                "created_at": new_chat.created_at.isoformat()
            })

    except WebSocketDisconnect:
        # 5. 연결 종료 시 관리자에서 제거
        manager.disconnect(websocket, room_id)
    finally:
        # DB 세션 닫기
        db_gen.close()

# 특정 방의 채팅 기록 가져오기 (과거 메시지 순서대로)
@app.get("/rooms/{room_id}/chats", response_model=List[schemas.ChatResponse])
def get_room_chats(room_id: int, limit: int = 50, db: Session = Depends(database.get_db)):
    """
    특정 방의 최근 채팅 기록을 최대 50개까지 가져옵니다.
    """
    chats = db.query(models.ChatMessage)\
            .filter(models.ChatMessage.room_id == room_id)\
            .order_by(models.ChatMessage.created_at.asc())\
            .limit(limit)\
            .all()
    return chats

# 노래 재생 상태 업데이트
@app.patch("/rooms/{room_id}/queue/{item_id}", response_model=schemas.QueueResponse)
def update_queue_item(room_id: int, item_id: int, is_played: bool, request_user_id: int, db: Session = Depends(database.get_db)):
    # 1. 해당 방 정보 가져오기
    db_room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found.")

    # 2. 요청자가 방장인지 확인
    if db_room.host_id != request_user_id:
        raise HTTPException(status_code=403, detail="Only the host can control the playback/queue.")

    # 3. 노래 항목 찾기
    db_item = db.query(models.QueueItem) \
        .filter(models.QueueItem.id == item_id, models.QueueItem.room_id == room_id) \
        .first()

    if not db_item:
        raise HTTPException(status_code=404, detail="The song cannot be found.")

    db_item.is_played = is_played
    db.commit()
    db.refresh(db_item)

    return db_item

