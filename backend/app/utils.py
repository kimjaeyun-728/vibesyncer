import yt_dlp

def extract_video_metadata(url: str):
    """
    Extract title, artist (channel), and thumbnail from a Youtube URL.
    Returns a dictionary or None if failed.
    """
    ydl_opts = {
        'quiet': True,              # Suppress console output
        'no_warnings': True,        # Ignore warning
        'format': 'bestaudio/best', # Prefer best audio quality (faster extraction)
        'extract_flat': True,       # Do not extract full playlist (process single video)
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Find the best quality thumbnail (fallback to None if not found)
            thumbnail = info.get('thumbnail', [])
            thumbnail_url = thumbnail[-1]['url'] if thumbnail else None

            return {
                "title": info.get('title', 'Unknown Title'),
                "artist": info.get('uploader', 'Unknown Artist'),
                "thumbnail_url": thumbnail_url
            }

    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return None