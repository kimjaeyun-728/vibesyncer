# backend/app/ai.py

import os
import re
import logging
import asyncio
from dotenv import load_dotenv
from datetime import datetime
from google import genai
from google.genai import types
from app.utils import search_youtube_video

logger = logging.getLogger(__name__)

load_dotenv(override=False)

# 전역 클라이언트는 처음에 비워둡니다 (Lazy Initialization)
client = None

def get_gemini_client():
    """구글 genai 라이브러리의 환경변수 꼬임 문제를 해결하기 위한 안전한 클라이언트 싱글톤 빌더"""
    global client
    if client is None:
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            logger.error("❌ [VibeBot Fatal] GEMINI_API_KEY is not found in system environment.")
            return None
        try:
            # 환경 변수가 확실히 준비된 시점에 명시적으로 주입하여 생성
            client = genai.Client(api_key=gemini_key)
            logger.info("✅ [VibeBot] Gemini Client initializing successful.")
        except Exception as e:
            logger.error(f"❌ [VibeBot] SDK Client Generation Failed: {e}")
            return None
    return client

# ==========================================
# Regex Patterns for Sanitization
# ==========================================
BOLD_PATTERN = re.compile(r'\*\*(.*?)\*\*')
CODE_BLOCK_PATTERN = re.compile(r'```[\s\S]*?```')
SONG_TAG_PATTERN = re.compile(r'\[\[SONG:.*?\]\]')
URL_PATTERN = re.compile(r'https?://\S+')

def sanitize_user_input(message: str) -> str:
    if not message: return ""
    clean_message = message.strip()
    if not clean_message: return ""
    clean_message = clean_message[:500]
    injection_patterns = [
        r'\[INSTRUCTION[S]?\]', r'\[SYSTEM\]', r'\[ROLE\]',
        r'\[CONTEXT\]', r'\[USER\]', r'ignore\s+(previous|above)\s+instructions?',
        r'disregard\s+(previous|above)',
    ]
    for pattern in injection_patterns:
        clean_message = re.sub(pattern, ' ', clean_message, flags=re.IGNORECASE)
    return clean_message.strip()

def sanitize_ai_response(response: str) -> str:
    if not response: return ""
    song_tags = SONG_TAG_PATTERN.findall(response)
    for i, tag in enumerate(song_tags):
        response = response.replace(tag, f"__SONG_PLACEHOLDER_{i}__")
    response = CODE_BLOCK_PATTERN.sub('', response)
    response = URL_PATTERN.sub('', response)
    response = BOLD_PATTERN.sub(r'\1', response)
    for i, tag in enumerate(song_tags):
        response = response.replace(f"__SONG_PLACEHOLDER_{i}__", tag)
    if len(response) > 1000:
        response = response[:997] + "..."
    return response.strip()

async def get_ai_dj_response(user_message: str, user_name: str, chat_history: list = [], current_queue: list = []) -> str:
    clean_message = sanitize_user_input(user_message)
    if not clean_message:
        return "🤖 I didn't catch that. Could you try again?"

    # ⚠️ 핵심: 실시간으로 준비된 안전한 클라이언트를 호출합니다.
    ai_client = get_gemini_client()
    if not ai_client:
        return "🤖 DJ Unavailable (API Key Missing)"

    now = datetime.now().strftime("%Y-%m-%d")
    history_text = ""
    if chat_history:
        history_text = "[Previous Conversation]\n"
        for msg in chat_history:
            sender = msg.get("username", "Unknown")
            content = msg.get("message", "")
            history_text += f"- {sender}: {content}\n"

    queue_text = "No music in queue."
    if current_queue:
        queue_titles = [f"{item['title']} - {item['artist']}" for item in current_queue]
        queue_text = ", ".join(queue_titles)

    try:
        prompt = f"""
        [Role]
        You are 'VibeBot', a smart AI DJ with access to Google Search.
        [Current Context]
        - **System Date**: {now}
        - **User**: {user_name}
        - **Current Queue (Now Playing/Next)**: {queue_text}
        {history_text}
        [User's Input]
        {user_name}: {user_message}
        [INSTRUCTIONS]
        1. **Intent Analysis**: Determine if the user wants a music recommendation or just chatting.
        2. **Music Recommendation Mode**:
           - Use Google Search to find the PERFECT song.
           - **CRITICAL RULE**: Do NOT generate the YouTube link yourself.
           - Instead, output a special tag: `[[SONG: Artist Name - Song Title]]`.
           - **Queue Awareness**: If a song is already in 'Current Queue', recommend something else!
        3. **Chat Mode**: Answer politely and wittily in 1-2 sentences.
        [OUTPUT FORMATS - STRICT]
        **Format (Music)**:
        [Artist] - [Title]
        [[SONG: Artist - Title]]
        (One sentence comment in Korean)
        **Format (Chat)**:
        (Polite answer in Korean)
        [Rules]
        - **Language**: Respond in the SAME language as the user's input.
        - No meta-talk. No Markdown bolding (`**`) for the song title.
        - **NEVER** output a URL starting with `https://`. Use the `[[SONG: ...]]` tag only.
        VibeBot:
        """

        # 안전하게 싱글톤 인스턴스로 비동기 쿼리 전송
        response = await ai_client.aio.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=600,
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )

        ai_text = response.text.strip()
        ai_text = sanitize_ai_response(ai_text)

        matches = re.findall(r"\[\[SONG: (.*?)\]\]", ai_text)
        for search_query in matches:
            real_url = await search_youtube_video(search_query)
            if real_url:
                replacement = f"(👉 Listen: {real_url})"
            else:
                replacement = f"(👉 Search: https://www.youtube.com/results?search_query={search_query.replace(' ', '+')})"
            ai_text = ai_text.replace(f"[[SONG: {search_query}]]", replacement)

        return ai_text

    except Exception as e:
        logger.error(f"AI DJ Error: {e}", exc_info=True)
        return "🤖 Sorry, I'm having trouble right now. Please try again later."

async def get_ai_welcome_message(username: str) -> str:
    ai_client = get_gemini_client()
    if not ai_client:
        return f"Hello {username}! Welcome to our music trip! 🎧"

    prompt = f"A new user named '{username}' just joined the room. Generate a short, fun, welcoming message in English (1 sentence, friendly, with emojis)."
    try:
        response = await ai_client.aio.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.8, max_output_tokens=100)
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"AI Welcome Error: {e}")
        return f"Hello {username}! Welcome to our music trip! 🎧"