import json
import logging
from pathlib import Path
from typing import Callable, Optional
from openai import OpenAI

from config import (
    LLM_STANDARD_API_KEY,
    LLM_BASE_URL,
    LLM_STANDARD_MODEL,
    LLM_TEMPERATURE,
    LLM_TOP_P,
    LLM_MAX_TOKENS,
    BASE_DIR,
    DB_PATH,
    TRANSCRIPTS_DIR
)
from db.schema import get_lecture, upsert_lecture

logger = logging.getLogger(__name__)


def get_llm_client() -> OpenAI:
    """Creates OpenAI client using configured LLM_BASE_URL and LLM_STANDARD_API_KEY."""
    return OpenAI(base_url=LLM_BASE_URL, api_key=LLM_STANDARD_API_KEY)


def load_prompt(prompt_name: str) -> str:
    """Loads prompt template from prompts/ directory."""
    prompt_path = BASE_DIR / "prompts" / prompt_name
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_concepts(
    transcript_text: str,
    lecture_id: str,
    course_context: str = "",
    stream_callback: Optional[Callable[[str], None]] = None,
    status_callback: Optional[Callable[[dict], None]] = None
) -> dict:
    """Sends transcript to DeepSeek V4 Pro with streaming and course context support."""
    client = get_llm_client()
    prompt_template = load_prompt("concept_extraction.txt")
    
    ctx_str = course_context if course_context else f"Lecture ID: {lecture_id}"
    prompt = prompt_template.replace("{course_context}", ctx_str).replace("{transcript}", transcript_text)
    
    logger.info(f"Extracting concepts for lecture {lecture_id} using {LLM_STANDARD_MODEL}...")
    
    from pipeline.resilient_llm import execute_resilient_llm_call
    from config import LLM_NON_STREAMING_TIMEOUT, DATA_DIR

    recovery_buffer = DATA_DIR / "recovery" / f"{lecture_id}_step2_stream.txt"
    messages = [{"role": "user", "content": prompt}]

    concepts, raw_text = execute_resilient_llm_call(
        client=client,
        model=LLM_STANDARD_MODEL,
        messages=messages,
        temperature=LLM_TEMPERATURE,
        top_p=LLM_TOP_P,
        max_tokens=LLM_MAX_TOKENS,
        stream=True,
        stream_callback=stream_callback,
        status_callback=status_callback,
        non_streaming_timeout=LLM_NON_STREAMING_TIMEOUT,
        save_buffer_path=recovery_buffer,
        fallback_list_key="problems_discussed"
    )

    return concepts


def process_extraction(
    lecture_id: str,
    course_context: str = "",
    stream_callback: Optional[Callable[[str], None]] = None,
    status_callback: Optional[Callable[[dict], None]] = None
) -> dict:
    """Loads transcript, calls extract_concepts with streaming & context, updates DB."""
    from datetime import datetime
    
    lecture = get_lecture(DB_PATH, lecture_id)
    if not lecture:
        raise ValueError(f"Lecture {lecture_id} not found in DB")
        
    transcript_path = lecture.get("transcript_path")
    if not transcript_path or not Path(transcript_path).exists():
        transcript_path = TRANSCRIPTS_DIR / f"{lecture_id}.json"
        if not transcript_path.exists():
            raise ValueError(f"Transcript for {lecture_id} not found at {transcript_path}")
            
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript_data = json.load(f)
        
    full_text = transcript_data.get("full_text") or transcript_data.get("text", "")
    if not full_text and transcript_data.get("segments"):
        full_text = "\n".join(s.get("text", "").strip() for s in transcript_data["segments"] if s.get("text"))
        
    if not full_text:
        raise ValueError(f"No text or segments found in transcript for {lecture_id}")
        
    concepts = extract_concepts(
        full_text,
        lecture_id,
        course_context=course_context,
        stream_callback=stream_callback,
        status_callback=status_callback
    )
    
    # Update DB
    lecture["topics"] = concepts.get("topics", [])
    lecture["techniques"] = concepts.get("techniques", [])
    lecture["difficulty"] = concepts.get("difficulty", "")
    lecture["key_moments"] = concepts.get("key_moments", [])
    lecture["problems_discussed"] = concepts.get("problems_discussed", [])
    lecture["status"] = "extracted"
    lecture["processed_at"] = datetime.now().isoformat()
    
    upsert_lecture(DB_PATH, lecture)
    
    return concepts
