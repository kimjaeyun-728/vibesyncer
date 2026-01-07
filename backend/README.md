---

### 📄 `backend/README.md`

```markdown
# 🎵 VibeSyncer Backend

**VibeSyncer** is a real-time collaborative platform where users can share music and chat in synchronized rooms. This repository contains the **FastAPI-based backend server** that powers the real-time features using WebSockets and PostgreSQL (Supabase).

---

## 🚀 Key Features

- **No-Login Access**: Users can create or join rooms instantly using just a nickname.
- **Room Lifecycle Management**:
  - **Create**: Auto-generates a unique 6-character Room Code (e.g., `X7A9Z1`).
  - **Join**: Easy access via Room Code.
  - **Dissolve**: Host can delete the room, automatically cleaning up all associated data (chat, queue, participants).
- **Real-Time Communication**: WebSocket-based chat and system notifications.
- **Collaborative Music Queue**:
  - Users can add songs via URL (YouTube, Spotify, etc.).
  - Supports album cover (thumbnail) display.
  - Real-time synchronization of the playlist across all clients.

---

## 🛠 Tech Stack

- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Database**: PostgreSQL (via Supabase)
- **ORM**: SQLAlchemy 2.0
- **Real-time**: WebSockets
- **Deployment**: Uvicorn (ASGI Server)

---

## 📂 Project Structure

The project follows a scalable directory structure:


```

backend/
├── app/
│   ├── main.py            # Entry point & API routes
│   ├── database.py        # DB connection & Session handling
│   ├── models/            # SQLAlchemy Database Models
│   └── schemas/           # Pydantic Data Schemas
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # Project documentation

```

---

## ⚡ Getting Started

### 1. Prerequisites
- Python 3.10 or higher installed.
- A Supabase account (or any PostgreSQL database).

### 2. Clone & Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd backend

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

```

### 3. Environment Configuration

Create a `.env` file in the root directory based on the example:

```bash
cp .env.example .env

```

Open `.env` and fill in your Supabase credentials:

```env
DATABASE_URL=postgresql://user:password@your-supabase-host:5432/postgres
SECRET_KEY=your_secret_key
ENVIRONMENT=development

```

### 4. Database Setup (Important)

Since we are using **Supabase**, please execute the following SQL in your Supabase SQL Editor to initialize the schema:

```sql
-- Create Tables implicitly via SQLAlchemy or run manual SQL if needed.
-- Ensure the following columns exist for the new features:
ALTER TABLE rooms ADD COLUMN IF NOT EXISTS room_code TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_rooms_room_code ON rooms(room_code);
ALTER TABLE queue_items ADD COLUMN IF NOT EXISTS thumbnail_url TEXT;

-- Allow duplicate nicknames globally (only unique per room)
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_username_key;
DROP INDEX IF EXISTS ix_users_username;
CREATE INDEX ix_users_username ON users(username);

```

### 5. Run the Server

```bash
uvicorn app.main:app --reload

```

* The server will start at `http://127.0.0.1:8000`.
* **API Documentation (Swagger UI)**: Visit `http://127.0.0.1:8000/docs`.

---

## 📝 API Endpoints Overview

| Method | Endpoint | Description |
| --- | --- | --- |
| **POST** | `/rooms/` | Create a new room & generate room code. |
| **POST** | `/rooms/join` | Join a room using a room code. |
| **POST** | `/rooms/leave` | Leave the current room. |
| **DEL** | `/rooms/{code}` | (Host) Dissolve the room & delete data. |
| **POST** | `/rooms/{id}/queue` | Add a song to the queue. |
| **WS** | `/ws/{id}/{uid}` | WebSocket connection for Chat & Updates. |

---

## 🤝 Contributing

1. Work on the `feature/init-be` branch.
2. Commit your changes with clear messages.
3. Push updates to the remote repository.

```