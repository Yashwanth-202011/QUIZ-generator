import os
import logging
from django.conf import settings
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

TRANSCRIPT_DIR = os.path.join(settings.BASE_DIR, 'generated', 'transcripts')
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

def generate_transcript(audio_path: str, video_id: str) -> str:
    """
    Transcribes the audio using faster-whisper.
    Returns the transcript text.
    """
    transcript_path = os.path.join(TRANSCRIPT_DIR, f"{video_id}.txt")
    
    if os.path.exists(transcript_path):
        with open(transcript_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    logger.info(f"Starting transcription for {video_id} using base model on CPU...")
    # Using base model, CPU execution since we want CPU compatibility (and offline)
    model = WhisperModel("base", device="cpu", compute_type="int8")
    
    segments, info = model.transcribe(audio_path, beam_size=5)
    
    transcript = []
    for segment in segments:
        transcript.append(segment.text)
        
    full_transcript = " ".join(transcript).strip()
    
    with open(transcript_path, 'w', encoding='utf-8') as f:
        f.write(full_transcript)
        
    logger.info("Transcription completed.")
    return full_transcript
