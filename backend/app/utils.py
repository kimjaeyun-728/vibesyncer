# backend/app/utils.py

import logging
import urllib.request
import re
import ssl
import yt_dlp
import string
import random
import os
import httpx
from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import models
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv(override=False)
# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=4)
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

def get_cookie_path():
    local_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies.txt')
    render_path = "/etc/secrets/cookies.txt"

    if os.path.exists(local_path):
        return local_path
    elif os.path.exists(render_path):
        return render_path
    else:
        return None

# ---------------------------------------------------------
# 1. New Utility: Room Code Generator
# ---------------------------------------------------------
def generate_room_code(length=6) -> str:
    """
    Generate a random alphanumeric string of fixed length.
    Used for creating unique room codes (e.g., 'A1B2C3').
    """
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for i in range(length))


# ---------------------------------------------------------
# 2. Existing Utility: Platform Detection
# ---------------------------------------------------------
def detect_platform(url: str):
    """
    Detect the platform from the URL string.
    """
    # [Debug] Print the URL being checked
    logger.debug(f" Checking URL: {url}")

    url_lower = url.lower()

    # 1. YouTube
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        logger.info("✅ Platform Detected: Youtube")
        return "Youtube"

    # 2. SoundCloud
    if "soundcloud.com" in url_lower:
        logger.info("✅ Platform Detected: Soundcloud")
        return "Soundcloud"

    # 3. Spotify
    if "spotify" in url_lower:
        logger.info("✅ Platform Detected: Spotify")
        return "Spotify"

    logger.warning("❌ Platform Detection Failed: Unsupported URL")
    return None


# ---------------------------------------------------------
# 3. Existing Utility: Spotify Scraper (Bypass DRM)
# ---------------------------------------------------------

async def fetch_spotify_metadata(url: str) -> Optional[Dict[str, Any]]:
    """
    [비동기 개선] httpx를 사용하여 Spotify HTML 페이지를 비동기적으로 스크래핑합니다.
    """
    logger.info(f"ℹ️ [Async] Scraping Spotify HTML for: {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # 비동기 클라이언트 생성 (SSL 검증 비활성화는 기존 ctx=ssl.create_default_context()... 설정과 동일)
        async with httpx.AsyncClient(verify=False, headers=headers) as client:
            response = await client.get(url, timeout=5.0)

            if response.status_code != 200:
                logger.warning(f"⚠️ Spotify scraping failed with status code: {response.status_code}")
                return None

            html_content = response.text

            # 메타데이터 추출 Regex 패턴 (기존 로직 유지)
            title_match = re.search(r'<meta property="og:title" content="(.*?)"', html_content)
            title = title_match.group(1) if title_match else "Unknown Title"

            thumbnail_match = re.search(r'<meta property="og:image" content="(.*?)"', html_content)
            thumbnail_url = thumbnail_match.group(1) if thumbnail_match else None

            artist = "Unknown Artist"
            desc_match = re.search(r'<meta property="og:description" content="(.*?)"', html_content)
            if desc_match:
                description = desc_match.group(1)
                if '·' in description:
                    artist = description.split('·')[0].strip()
                else:
                    artist = description

            logger.info(f"🎉 [Async Spotify Scraper] Success! Title: {title} / Artist: {artist}")

            return {
                "title": title,
                "artist": artist,
                "thumbnail_url": thumbnail_url
            }

    except Exception as e:
        logger.error(f"💥 [Spotify Error] Async HTML scraping failed: {e}")
        return None


def extract_youtube_id(url: str):
    """
    Extracts the video ID from various YouTube URL formats.
    Supports: youtube.com/watch?v=ID, youtu.be/ID, shorts/ID
    """
    # 1. Short URL (youtu.be/ID)
    if "youtu.be" in url:
        path = urlparse(url).path
        return path[1:] if path else None

    # 2. Standard URL (youtube.com/watch?v=ID)
    if "youtube.com" in url:
        query = urlparse(url).query
        params = parse_qs(query)
        return params.get("v", [None])[0]

    return None

# ---------------------------------------------------------
# 4. Existing Utility: General Metadata Extractor
# ---------------------------------------------------------
# ---------------------------------------------------------
# [Modified] 4. General Metadata Extractor
# ---------------------------------------------------------
async def extract_video_metadata(url: str):
    """
    [비동기 개선] 각 플랫폼별 메타데이터 추출 함수를 비동기적으로 분기 처리합니다.
    """
    logger.info(f"🚀 Starting Async Metadata Extraction for: {url}")

    # STRATEGY 1: Spotify (Custom Scraper - Async)
    if "spotify" in url.lower():
        return await fetch_spotify_metadata(url)

    # STRATEGY 2: YouTube (Google Data API - Async)
    if "youtube.com" in url.lower() or "youtu.be" in url.lower():
        return await fetch_youtube_metadata_api(url)

    # STRATEGY 3: SoundCloud & Others (yt-dlp Fallback - 여전히 동기이므로 루프 스레드 활용)
    return await asyncio.to_thread(fetch_metadata_with_ytdlp, url)


async def fetch_youtube_metadata_api(url: str) -> Optional[Dict[str, Any]]:

    if not GOOGLE_API_KEY:
        logger.error("🚫 GOOGLE_API_KEY is missing! Cannot fetch metadata.")
        return None

    video_id = extract_youtube_id(url)
    if not video_id:
        logger.warning(f"⚠️ Could not extract Video ID from: {url}")
        return None

    # YouTube Data API v3의 videos 엔드포인트 URL
    api_url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,contentDetails",
        "id": video_id,
        "key": GOOGLE_API_KEY
    }

    try:
        # httpx 비동기 클라이언트로 GET 요청 전달
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, params=params, timeout=5.0)

            if response.status_code != 200:
                logger.error(f"💥 [Google API Error] HTTP Status {response.status_code}: {response.text}")
                return None

            data = response.json()

        items = data.get("items", [])
        if not items:
            logger.warning("⚠️ API returned no details for this video.")
            return None

        snippet = items[0]["snippet"]

        title = snippet.get("title", "Unknown Title")
        artist = snippet.get("channelTitle", "Unknown Artist")

        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = (
                thumbnails.get("maxres", {}).get("url") or
                thumbnails.get("high", {}).get("url") or
                thumbnails.get("default", {}).get("url")
        )

        logger.info(f"🎉 [Async Google API] Success! Title: {title}")

        return {
            "title": title,
            "artist": artist,
            "thumbnail_url": thumbnail_url
        }

    except Exception as e:
        logger.error(f"💥 [Google API Exception] {e}")
        return None

def fetch_metadata_with_ytdlp(url: str):
    """
    Legacy yt-dlp method for non-YouTube platforms (e.g. SoundCloud).
    """
    logger.info(f"ℹ️ Attempting yt-dlp for non-YouTube URL: {url}")

    cookie_path = get_cookie_path()

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestaudio/best',
        'ignoreerrors': True,
        'no_playlist': True,
        'nocheckcertificate': True,
        'cookiefile': cookie_path,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info: return None

            return {
                "title": info.get('title', 'Unknown Title'),
                "artist": info.get('uploader') or info.get('artist') or 'Unknown Artist',
                "thumbnail_url": info.get('thumbnail')
            }
    except Exception as e:
        logger.error(f"💥 [yt-dlp Error] {e}")
        return None


# ---------------------------------------------------------
# 5. Existing Utility: YouTube Search (For AI DJ)
# ---------------------------------------------------------
async def search_youtube_video(query: str) -> Optional[str]:
    """
    [비동기 개선] 구글 동기 라이브러리 대신 httpx를 사용하여
    YouTube Data API v3에서 비동기로 영상을 검색하고 첫 번째 결과의 URL을 반환합니다.
    """
    logger.info(f"🔍 [Async API Search] Searching YouTube for: {query}")

    if not GOOGLE_API_KEY:
        logger.error("🚫 GOOGLE_API_KEY is missing! Cannot search.")
        return None

    # YouTube Data API v3의 search 엔드포인트 URL
    api_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "q": query,
        "part": "id,snippet",
        "maxResults": 1,
        "type": "video",
        "key": GOOGLE_API_KEY
    }

    try:
        # httpx 비동기 클라이언트로 GET 요청 전달
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, params=params, timeout=5.0)

            if response.status_code != 200:
                logger.error(f"💥 [API Search Error] HTTP Status {response.status_code}: {response.text}")
                return None

            data = response.json()

        items = data.get('items', [])
        if not items:
            logger.warning(f"⚠️ [Async API Search] No results found for: {query}")
            return None

        video_id = items[0]['id']['videoId']
        video_title = items[0]['snippet']['title']

        video_url = f"https://www.youtube.com/watch?v={video_id}"
        logger.info(f"✅ [Async API Search] Found: {video_title} ({video_url})")

        return video_url

    except Exception as e:
        logger.error(f"💥 [Search Error] {e}")
        return None

# ---------------------------------------------------------
# 6. New Utility: Process Music Addition (Moved from main.py)
# ---------------------------------------------------------
async def process_music_addition(
        room_id: int,
        user_id: int,
        music_url: str,
        db: Session,
        thumbnail_url: Optional[str] = None,
        title: str = "Unknown Title",
        artist: str = "Unknown Artist"
) -> Optional[models.QueueItem]:
    """
    [비동기 개선] 방에 음악 아이템을 추가하는 비즈니스 로직입니다.
    완전 비동기화된 extract_video_metadata를 await로 직접 호출합니다.
    """
    # 1. 플랫폼 감지 (단순 문자열 비교이므로 동기 유지)
    detected_platform = detect_platform(music_url)

    if not detected_platform:
        return None

    # 2. 메타데이터 추출 비동기 호출
    TARGET_PLATFORMS = ["Youtube", "Soundcloud", "Spotify"]

    if detected_platform in TARGET_PLATFORMS:
        if title == "Unknown Title" or title.startswith("Shared by"):
            # [개선] loop나 executor 없이 깔끔하게 await로 메타데이터를 가져옵니다.
            metadata = await extract_video_metadata(music_url)

            if metadata:
                title = metadata.get("title", title)
                artist = metadata.get("artist", artist)
                if not thumbnail_url:
                    thumbnail_url = metadata.get("thumbnail_url")

    # 3. 데이터베이스 저장 (SQLAlchemy 동기 세션 유지)
    db_item = models.QueueItem(
        room_id=room_id,
        user_id=user_id,
        title=title,
        artist=artist,
        music_url=music_url,
        thumbnail_url=thumbnail_url,
        platform=detected_platform,
        is_played=False
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item

def shutdown_executor():
    logger.info("Shutting down ThreadPoolExecutor...")
    executor.shutdown(wait=True)
    logger.info("ThreadPoolExecutor shutdown complete.")