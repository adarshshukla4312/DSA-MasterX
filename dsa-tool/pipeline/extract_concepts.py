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
    stream_callback: Optional[Callable[[str], None]] = None
) -> dict:
    """Sends transcript to DeepSeek V4 Pro with streaming and course context support."""
    client = get_llm_client()
    prompt_template = load_prompt("concept_extraction.txt")
    
    ctx_str = course_context if course_context else f"Lecture ID: {lecture_id}"
    prompt = prompt_template.replace("{course_context}", ctx_str).replace("{transcript}", transcript_text)
    
    logger.info(f"Extracting concepts for lecture {lecture_id} using {LLM_STANDARD_MODEL}...")
    
    response_text = ""
    last_exception = None

    for attempt in range(1, 4):
        try:
            try:
                response_stream = client.chat.completions.create(
                    model=LLM_STANDARD_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=LLM_TEMPERATURE,
                    top_p=LLM_TOP_P,
                    max_tokens=LLM_MAX_TOKENS,
                    stream=True
                )
                
                full_chunks = []
                for chunk in response_stream:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        text_chunk = chunk.choices[0].delta.content
                        full_chunks.append(text_chunk)
                        if stream_callback:
                            stream_callback(text_chunk)
                            
                response_text = "".join(full_chunks)
            except Exception as stream_err:
                logger.warning(f"Streaming LLM call attempt {attempt} failed ({stream_err}), trying stream=False...")
                completion = client.chat.completions.create(
                    model=LLM_STANDARD_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=LLM_TEMPERATURE,
                    top_p=LLM_TOP_P,
                    max_tokens=LLM_MAX_TOKENS,
                    stream=False
                )
                response_text = completion.choices[0].message.content
            
            if response_text.strip():
                break
        except Exception as e:
            last_exception = e
            err_str = str(e).lower()
            logger.warning(f"LLM extraction attempt {attempt}/3 failed: {e}")
            if attempt < 3:
                import time
                sleep_time = 2 ** attempt
                if "429" in err_str or "rate limit" in err_str:
                    sleep_time = 10 * attempt
                elif "timeout" in err_str:
                    sleep_time = 5 * attempt
                time.sleep(sleep_time)
            else:
                raise last_exception

    # Try to parse JSON from the response
    try:
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
            
        concepts = json.loads(clean_text.strip())
        return concepts
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response for {lecture_id}: {e}\nResponse: {response_text}")
        raise ValueError("LLM response was not valid JSON") from e


def process_extraction(
    lecture_id: str,
    course_context: str = "",
    stream_callback: Optional[Callable[[str], None]] = None
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
        stream_callback=stream_callback
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
