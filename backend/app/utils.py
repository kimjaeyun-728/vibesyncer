import logging
import urllib.request
import re
import ssl
import yt_dlp

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def detect_platform(url: str):
    """
    Detect the platform from the URL string.
    """
    # [Debug] Print the URL being checked
    # [Fix 2] print -> logger.debug/info
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


def fetch_spotify_metadata(url: str):
    """
    Fetch metadata by scraping the Spotify HTML page directly.
    This bypasses DRM errors from yt-dlp.
    """
    logger.info(f"ℹ️ Scraping Spotify HTML for: {url}")

    try:
        # 1. Prepare Request with User-Agent (mimic a real browser)
        req = urllib.request.Request(
            url,
            data=None,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )

        # 2. Create SSL context to ignore certificate errors
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        # 3. Read HTML Content
        with urllib.request.urlopen(req, context=ctx) as response:
            html_content = response.read().decode('utf-8')

            # 4. Extract Metadata using Regex (Open Graph tags)
            # Title: <meta property="og:title" content="Song Title" />
            title_match = re.search(r'<meta property="og:title" content="(.*?)"', html_content)
            title = title_match.group(1) if title_match else "Unknown Title"

            # Thumbnail: <meta property="og:image" content="https://..." />
            thumbnail_match = re.search(r'<meta property="og:image" content="(.*?)"', html_content)
            thumbnail_url = thumbnail_match.group(1) if thumbnail_match else None

            # Artist: Found in 'og:description' usually as "Artist · Song · Year"
            # <meta property="og:description" content="Rick Astley · Song · 1987" />
            artist = "Unknown Artist"
            desc_match = re.search(r'<meta property="og:description" content="(.*?)"', html_content)
            if desc_match:
                description = desc_match.group(1)
                # Split by '·' and take the first part (Artist Name)
                if '·' in description:
                    artist = description.split('·')[0].strip()
                else:
                    artist = description  # Fallback

            logger.info(f"🎉 [Spotify Scraper] Success! Title: {title} / Artist: {artist}")

            return {
                "title": title,
                "artist": artist,
                "thumbnail_url": thumbnail_url
            }

    except Exception as e:
        logger.error(f"💥 [Spotify Error] HTML scraping failed: {e}")
        return None


def extract_video_metadata(url: str):
    logger.info(f"🚀 Starting Metadata Extraction for: {url}")

    # ---------------------------------------------------------
    # STRATEGY 1: Use Custom Scraper for Spotify (Bypass DRM)
    # ---------------------------------------------------------
    if "spotify" in url.lower():
        return fetch_spotify_metadata(url)

    # ---------------------------------------------------------
    # STRATEGY 2: Use yt-dlp for YouTube & SoundCloud
    # ---------------------------------------------------------
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestaudio/best',
        'ignoreerrors': True,
        'no_playlist': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if not info:
                logger.info(f"❌ [DEBUG] Extraction Failed: Info is empty")
                return None

            if 'entries' in info:
                entries = list(info['entries'])
                info = entries[0] if entries else None
                if not info: return None

            title = info.get('title', 'Unknown Title')

            # Try to find artist in various fields
            artist = info.get('artist') or info.get('uploader') or info.get('creator') or info.get(
                'channel') or 'Unknown Artist'

            thumbnail_url = info.get('thumbnail')
            thumbnails = info.get('thumbnails', [])
            if thumbnails:
                thumbnail_url = thumbnails[-1].get('url')

            logger.info(f"🎉 [yt-dlp] Success! Title: {title} / Artist: {artist}")

            return {
                "title": title,
                "artist": artist,
                "thumbnail_url": thumbnail_url
            }

    except Exception as e:
        logger.error(f"💥 Critical Error during extraction: {e}")
        return None


# backend/app/utils.py

def search_youtube_video(query: str):
    """
    Search YouTube via yt-dlp and return the URL of the first result.

    Keyword arguments:
    query -- Search query string (e.g., "NewJeans Hype Boy")
    """
    logger.info(f"🔍 [Backend Search] Searching YouTube for: {query}")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        # [Fix 1] Use 'default_search' option instead of manual prefix string
        'default_search': 'ytsearch1',
        'noplaylist': True,
        # [Fix 2] REMOVED 'allowed_extractors'.
        # This was blocking the 'ytsearch:' protocol because it's not a standard URL.
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # [Fix 3] Pass the raw query string directly (e.g., "Artist - Title")
            # yt-dlp will automatically apply 'ytsearch1:' due to 'default_search' option.
            info = ydl.extract_info(query, download=False)

            # When searching, the result is usually inside 'entries'
            if 'entries' in info and info['entries']:
                video_url = info['entries'][0].get('webpage_url')
                logger.info(f"✅ [Backend Search] Found URL: {video_url}")
                return video_url

            # Fallback: Sometimes info itself is the video info
            elif 'webpage_url' in info:
                video_url = info['webpage_url']
                logger.info(f"✅ [Backend Search] Found URL: {video_url}")
                return video_url

            else:
                logger.info(f"⚠️ [Backend Search] No results found for: {query}")

    except Exception as e:
        logger.error(f"💥 [Backend Search Error] {e}")

    return None