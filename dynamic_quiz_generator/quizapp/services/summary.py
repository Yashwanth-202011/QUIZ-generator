import os
import logging
import spacy
from keybert import KeyBERT
from django.conf import settings

logger = logging.getLogger(__name__)

SUMMARY_DIR = os.path.join(settings.BASE_DIR, 'generated', 'summaries')
os.makedirs(SUMMARY_DIR, exist_ok=True)

# Load spacy model and KeyBERT
try:
    nlp = spacy.load("en_core_web_sm")
except ImportError:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

kw_model = KeyBERT()

def extract_concepts(transcript_text: str, video_id: str, title: str = "Unknown Title") -> str:
    """
    Cleans transcript, extracts key concepts and returns a condensed version.
    """
    summary_path = os.path.join(SUMMARY_DIR, f"{video_id}_summary.txt")
    
    if os.path.exists(summary_path):
        with open(summary_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    logger.info(f"Extracting concepts for {video_id}...")
    
    # Simple cleaning with spacy
    doc = nlp(transcript_text[:100000]) # Limit length for performance if needed
    sentences = [sent.text for sent in doc.sents]
    
    # Extract keywords
    keywords = kw_model.extract_keywords(transcript_text, keyphrase_ngram_range=(1, 3), stop_words='english', top_n=15)
    kw_str = ", ".join([kw[0] for kw in keywords])
    
    # In a full production system, we'd do more extensive summarization (extractive/abstractive)
    # But since we're passing it to an LLM, reducing the token count by stripping out 
    # overly conversational filler and prioritizing the core sentences/keywords is good.
    # For now, we package the raw text with the keywords to guide the LLM better.
    
    summarized_content = (
        f"VIDEO TITLE:\n{title}\n\n"
        f"KEY CONCEPTS:\n{kw_str}\n\n"
        f"TRANSCRIPT CONTENT:\n{transcript_text}"
    )
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summarized_content)
        
    logger.info("Extraction completed.")
    return summarized_content
