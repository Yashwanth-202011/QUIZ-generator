import yt_dlp
import urllib.parse
import re
import logging

logger = logging.getLogger(__name__)

def is_valid_youtube_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(url)
        if 'youtube' in parsed.hostname or 'youtu.be' in parsed.hostname:
            return True
        return False
    except:
        return 'youtube.com' in url or 'youtu.be' in url

def extract_youtube_id(url: str) -> str:
    """Safely regex extracts the exact 11-character YouTube Video ID"""
    patterns = [
        r"(?:v=|\/shorts\/|\/embed\/|youtu\.be\/|\/v\/|\/e\/|watch\?v=|&v=)([^#\&\?]{11})",
        r"youtube\.com\/shorts\/([^\/\?]+)",
        r"youtu\.be\/([^\/\?]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_metadata(url: str) -> dict:
    if not is_valid_youtube_url(url):
        raise ValueError("Please provide a valid YouTube link (e.g., youtube.com/watch?v=... or youtu.be/...)")

    video_id = extract_youtube_id(url)

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(url, download=False)
                
                # Prefer the exact regex ID for embedding to prevent Error 153 iframe crashes
                final_id = video_id if video_id else info_dict.get('id')
                
                if not final_id:
                    raise ValueError("Failed to extract Video ID.")
                    
                # If thumbnail is missing, construct the default one using the ID
                thumbnail = info_dict.get('thumbnail')
                if not thumbnail:
                    thumbnail = f"https://img.youtube.com/vi/{final_id}/hqdefault.jpg"
                    
                return {
                    'video_id': final_id,
                    'title': info_dict.get('title', 'YouTube Video'),
                    'thumbnail': thumbnail
                }
            except Exception as e:
                # Fallback: if yt-dlp fails (e.g. Bot detection), but we have a regex ID, we can still proceed
                if video_id:
                    logger.warning(f"yt-dlp metadata extraction failed ({e}). Using regex fallback ID.")
                    return {
                        'video_id': video_id,
                        'title': "YouTube Video",
                        'thumbnail': f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                    }
                raise e
    except Exception as e:
        logger.error(f"Metadata extraction error: {e}")
        raise ValueError("The provided url is unsupported or private.")
