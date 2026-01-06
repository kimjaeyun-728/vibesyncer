# vibesyncer

프론트엔드 동료가 바로 개발에 착수할 수 있도록, **Git Strategy** 가이드라인을 준수하여 `README.md`에 꼭 들어가야 하는 내용만 정리해 드립니다. 아래 내용을 그대로 복사해서 사용하세요.

---

# 🎵 VibeSyncer - Backend

VibeSyncer는 실시간 음악 큐 공유 및 채팅 플랫폼입니다. 이 서버는 **FastAPI**와 **Supabase**를 기반으로 구축되었습니다.

## 🛠 Tech Stack

* **Framework**: FastAPI (Python)
* **Database**: PostgreSQL (Supabase)
* **ORM**: SQLAlchemy
* **Real-time**: WebSocket

## 🚀 Getting Started

### 1. Installation

```bash
pip install -r requirements.txt

```

### 2. Environment Variables

프로젝트 루트에 `.env` 파일을 생성하세요.

> 
> **⚠️ 주의**: 로컬 설정 파일(`.env`)은 절대 Git에 커밋하지 마세요.
> 
> 

```env
DATABASE_URL=your_supabase_postgresql_url

```

### 3. Running the Server

사무실 내 다른 기기에서의 접속을 허용하려면 다음 명령어를 사용하세요.

```bash
uvicorn main:app --host 0.0.0.0 --port 8000

```

* **API Documentation**: [http://localhost:8000/docs](https://www.google.com/search?q=http://localhost:8000/docs) (Swagger UI)

---

## 🌿 Git Strategy & Workflow

본 프로젝트는 공식 가이드라인에 따라 **GitLab Flow** 전략을 따릅니다.

Branching Model 

* 
**main**: 실제 서비스(Production) 환경 배포용 브랜치.


* 
**staging**: 배포 전 최종 테스트 환경 (Pre-production).


* 
**test**: QA를 위한 테스트 환경.


* 
**develop**: 현재 개발 중인 기능들이 통합되는 메인 브랜치.


* 
**feature/**: 새로운 기능을 개발하는 브랜치 (예: `feature/user-login`).



Commit Message Convention 

**Conventional Commits** 사양을 준수합니다.

* 
`feat`: 새로운 기능 추가.


* 
`fix`: 버그 수정.


* 
`docs`: 문서 수정 (README 등).


* 
`chore`: 설정 변경, 패키지 관리 등.


* 
`refactor`: 코드 리팩토링.



---

## 🔌 API & WebSocket Specifications

### WebSocket Endpoint

* **URL**: `ws://{server_ip}:8000/ws/{room_id}/{user_id}`
* **Features**:
* DB 유저 정보와 연동된 실시간 채팅 브로드캐스트.
* 음악 큐 업데이트 실시간 동기화 알림.



### Playback Authorization

* **방장(Room Host)** 만 노래 재생 상태를 업데이트(PATCH)할 수 있습니다.
* 권한이 없는 사용자의 요청은 **403 Forbidden** 에러를 반환합니다.

---

## 📂 Project Structure

* `main.py`: FastAPI 앱 설정 및 웹소켓 엔드포인트.
* `models.py`: SQLAlchemy 데이터베이스 모델.
* `schemas.py`: Pydantic 모델 및 Swagger UI 메타데이터.
* `database.py`: DB 연결 및 세션 관리.

---