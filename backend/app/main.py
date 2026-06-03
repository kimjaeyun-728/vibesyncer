# backend/app/main.py

import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import Database & Models
from app import database
from app.models import models

# Import Routers
from app.api.routes import rooms, websockets
from app.utils import shutdown_executor

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

gemini_key = os.environ.get("GEMINI_API_KEY")
google_key = os.environ.get("GOOGLE_API_KEY")

logger.info(f"🚨 [CRITICAL CHECK] GEMINI_API_KEY: {gemini_key[:4] if gemini_key else 'NOT_FOUND'}")
logger.info(f"🚨 [CRITICAL CHECK] GOOGLE_API_KEY: {google_key[:4] if google_key else 'NOT_FOUND'}")

if not gemini_key or not google_key:
    logger_msg = "❌ [FATAL] 필수 환경 변수가 시스템에 존재하지 않습니다. Render 설정을 확인하세요."
    logger.error(logger_msg)

# Initialize FastAPI App
app = FastAPI(
    title="VibeSyncer API",
    description="Real-time collaborative music platform with WebSocket support",
    version="0.1.0"
)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Startup Events
# ---------------------------------------------------------
BOT_USER_ID = 0


@app.on_event("startup")
def startup_event():
    """
    Execute tasks on application startup.
    1. Create Database Tables (if not exist)
    2. Ensure System Bot User exists
    """
    # 1. Create Tables
    models.Base.metadata.create_all(bind=database.engine)

    # 2. Check/Create Bot User
    db = database.SessionLocal()
    try:
        bot_user = db.query(models.User).filter(models.User.id == BOT_USER_ID).first()
        if not bot_user:
            logger.info(f"🤖 Creating System Bot User (ID: {BOT_USER_ID})...")
            bot_user = models.User(id=BOT_USER_ID, username="🤖 VibeBot")
            db.add(bot_user)
            db.commit()
            logger.info("✅ System Bot User created successfully!")
        else:
            logger.info(f"✅ System Bot User (ID: {BOT_USER_ID}) is ready.")
    except Exception as e:
        logger.error(f"⚠️ Warning: Failed to check/create bot user. Error: {e}")
    finally:
        db.close()

@app.on_event("shutdown")
async def shutdown_event():
    shutdown_executor()

# ---------------------------------------------------------
# Register Routers
# ---------------------------------------------------------
# Room related APIs -> /rooms/...
app.include_router(rooms.router, prefix="/rooms", tags=["rooms"])

# WebSocket APIs -> /ws/...
app.include_router(websockets.router, tags=["websockets"])


# ---------------------------------------------------------
# Root Endpoint (Health Check)
# ---------------------------------------------------------
@app.get("/")
def read_root():
    return {"message": "VibeSyncer Backend is Running!"}