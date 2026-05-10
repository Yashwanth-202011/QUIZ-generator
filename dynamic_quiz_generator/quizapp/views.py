import json
import logging
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest

from .services.youtube import get_video_metadata
from .services.audio import download_and_convert_audio
from .services.transcription import generate_transcript
from .services.summary import extract_concepts
from .services.validation import generate_and_validate_quiz

logger = logging.getLogger(__name__)

def index(request):
    """Renders the home page."""
    return render(request, 'quizapp/index.html')

def process_video(request):
    """
    Handles the form submission or AJAX request.
    Extracts metadata and renders the processing page.
    """
    if request.method == 'POST':
        url = request.POST.get('url') or json.loads(request.body).get('url')
        if not url:
            return HttpResponseBadRequest("URL is required")
        
        try:
            metadata = get_video_metadata(url)
            # Render processing page with metadata
            return render(request, 'quizapp/processing.html', {
                'metadata': metadata,
                'url': url
            })
        except Exception as e:
            logger.error(f"Error processing video URL: {e}")
            return render(request, 'quizapp/index.html', {'error': str(e)})
            
    return render(request, 'quizapp/index.html')

def generate_quiz_api(request):
    """
    The main API endpoint that runs the sequential pipeline:
    download audio -> transcribe -> extract concepts -> llm -> validate
    Returns JSON.
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST allowed"}, status=405)
        
    try:
        data = json.loads(request.body)
        url = data.get('url')
        video_id = data.get('video_id')
        
        if not url or not video_id:
            return JsonResponse({"error": "URL and Video ID are required"}, status=400)
            
        logger.info(f"Pipeline started for {video_id}")
        
        title = data.get('title', 'Unknown Title')
        
        # 1. Download & Convert
        audio_path = download_and_convert_audio(url, video_id)
        
        # 2. Transcribe
        transcript_text = generate_transcript(audio_path, video_id)
        
        # 3. Extract Concepts
        summarized_content = extract_concepts(transcript_text, video_id, title)
        
        # 4 & 5. Generate and Validate JSON Quiz
        quiz_data = generate_and_validate_quiz(summarized_content, video_id)
        
        logger.info(f"Pipeline finished for {video_id}")
        return JsonResponse(quiz_data)
        
    except Exception as e:
        logger.error(f"Error during generative pipeline: {e}")
        return JsonResponse({"error": str(e)}, status=500)

def quiz_view(request):
    """Renders the quiz taking interface."""
    return render(request, 'quizapp/quiz.html')

def result_view(request):
    """Renders the result view."""
    return render(request, 'quizapp/result.html')
