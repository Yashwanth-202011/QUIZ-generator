import json
import logging
import os
from typing import List
from pydantic import BaseModel, ValidationError
from django.conf import settings
from .llm import generate_quiz_from_llm

logger = logging.getLogger(__name__)

QUIZ_DIR = os.path.join(settings.BASE_DIR, 'generated', 'quizzes')
os.makedirs(QUIZ_DIR, exist_ok=True)

class Question(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str

class QuizModel(BaseModel):
    quiz: List[Question]

def validate_and_repair_json(raw_json: str) -> dict:
    """
    Parses string to JSON. Validates format through Pydantic.
    Attempts minor repairs if necessary.
    """
    # Remove any potential markdown block wrappers
    raw_json = raw_json.strip()
    if raw_json.startswith("```json"):
        raw_json = raw_json[7:]
    if raw_json.endswith("```"):
        raw_json = raw_json[:-3]
    raw_json = raw_json.strip()
        
    try:
        parsed = json.loads(raw_json)
        # Validate with Pydantic
        quiz_data = QuizModel(**parsed)
        return quiz_data.model_dump()
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}. Raw content: {raw_json}")
        raise ValueError("Invalid JSON format returned from LLM.")
    except ValidationError as e:
        logger.error(f"JSON structure validation failed: {e}")
        raise ValueError("JSON does not conform to the required quiz schema.")

def generate_and_validate_quiz(context: str, video_id: str, retries: int = 2) -> dict:
    quiz_path = os.path.join(QUIZ_DIR, f"{video_id}_quiz.json")
    
    if os.path.exists(quiz_path):
        with open(quiz_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    for attempt in range(retries):
        try:
            logger.info(f"Generating quiz for {video_id}, attempt {attempt+1}...")
            raw_response = generate_quiz_from_llm(context)
            valid_quiz = validate_and_repair_json(raw_response)
            
            with open(quiz_path, 'w', encoding='utf-8') as f:
                json.dump(valid_quiz, f, indent=2)
                
            return valid_quiz
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed: {e}")
            
    raise RuntimeError("Failed to generate a valid quiz after multiple attempts.")
