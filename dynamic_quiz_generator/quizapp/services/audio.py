import os
import subprocess
import logging
from django.conf import settings
import yt_dlp

logger = logging.getLogger(__name__)

AUDIO_DIR = os.path.join(settings.BASE_DIR, 'generated', 'audio')

def download_and_convert_audio(video_url: str, video_id: str) -> str:
    """
    Downloads audio using yt-dlp. 
    Faster-Whisper natively decodes standard formats (like webm, m4a) via its AV backend, 
    so we can skip the manual FFmpeg subprocess entirely and avoid WinError 2.
    """
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    # Use yt-dlp's dynamic extension formatting
    audio_path_tmpl = os.path.join(AUDIO_DIR, f"{video_id}.%(ext)s")

    # If already downloaded, return it
    for f in os.listdir(AUDIO_DIR):
        if f.startswith(f"{video_id}.") and not f.endswith(".part"):
            return os.path.join(AUDIO_DIR, f)

    # Download best audio
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': audio_path_tmpl,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
    }
    
    logger.info(f"Downloading audio for {video_id} without FFmpeg conversion...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
        
    for f in os.listdir(AUDIO_DIR):
        if f.startswith(f"{video_id}.") and not f.endswith(".part"):
            return os.path.join(AUDIO_DIR, f)
            
    raise FileNotFoundError("Audio download failed.")
