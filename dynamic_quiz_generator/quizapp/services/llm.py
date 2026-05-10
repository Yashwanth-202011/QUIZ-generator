import requests
import json
import logging
from django.conf import settings

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

logger = logging.getLogger(__name__)

def generate_quiz_from_llm(context: str, num_questions: int = 5) -> str:
    """
    Sends the summarized transcript to Gemini API if available, 
    otherwise falls back to the local Qwen 2.5 Ollama instance.
    Requests raw JSON output.
    """
    prompt = f"""
You are an educational quiz generator.

Generate {num_questions} multiple choice quiz questions from the provided content.

IMPORTANT RULES:
1. Return ONLY valid JSON
2. No markdown
3. No extra text
4. No explanations outside JSON

CONTENT:
{context}

JSON FORMAT:
{{
  "quiz": [
    {{
      "question": "...",
      "options": [
        "...",
        "...",
        "...",
        "..."
      ],
      "correct_answer": "...",
      "explanation": "..."
    }}
  ]
}}
"""

    if GENAI_AVAILABLE and getattr(settings, 'GEMINI_API_KEY', None):
        try:
            logger.info("Attempting to generate quiz using Gemini API...")
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            response = model.generate_content(prompt)
            response_text = response.text
                
            return response_text
        except Exception as e:
            logger.warning(f"Gemini API failed ({e}). Falling back to Groq model.")

    if GROQ_AVAILABLE and getattr(settings, 'GROQ_API_KEY', None):
        try:
            logger.info("Using Groq model for fallback quiz generation.")
            client = Groq(api_key=settings.GROQ_API_KEY)
            
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=1,
                max_completion_tokens=4096,
                top_p=1,
                stream=True,
                stop=None
            )
            
            response_text = ""
            for chunk in completion:
                response_text += chunk.choices[0].delta.content or ""
            
            # Extract JSON block if surrounded by markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[-1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[-1].split("```")[0].strip()

            return response_text
        except Exception as e:
            logger.error(f"Error communicating with Groq: {e}")
            raise RuntimeError("Failed to generate quiz from LLM.")
    else:
        logger.error("Groq API not available or configured.")
        raise RuntimeError("Failed to generate quiz from LLM.")
