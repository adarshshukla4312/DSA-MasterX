import json
import logging
import sqlite3
from pathlib import Path
from typing import Callable, Optional

from openai import OpenAI
from config import (
    DB_PATH,
    LLM_REASONING_API_KEY,
    LLM_REASONING_MODEL,
    LLM_BASE_URL,
    LLM_TEMPERATURE,
    LLM_TOP_P,
    LLM_MAX_TOKENS,
    BASE_DIR
)
from db.schema import get_lecture, get_all_problems, upsert_lecture, get_connection
from pipeline.match_db import find_candidates, store_candidates
from pipeline.extract_concepts import get_llm_client, load_prompt
from pipeline.pipeline_version import compute_pipeline_hash

logger = logging.getLogger(__name__)


def auto_insert_discovered_problem(prob_data: dict, db_path: str | Path) -> str | None:
    """Inserts a newly discovered problem into the DB if not present."""
    if not prob_data or not isinstance(prob_data, dict):
        return None

    title = prob_data.get("title", "Discovered Problem")
    platform = prob_data.get("platform", "LeetCode")
    url = prob_data.get("url", "")
    difficulty = prob_data.get("difficulty", "Medium")
    patterns = prob_data.get("patterns", [])
    desc = prob_data.get("description", "")
    
    raw_id = prob_data.get("id") or title.lower().replace(" ", "-").replace("_", "-")
    prob_id = "".join(c for c in raw_id if c.isalnum() or c == "-")[:40]
    if not prob_id.startswith(("lc-", "gfg-", "auto-")):
        prob_id = f"auto-{prob_id}"

    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT OR IGNORE INTO problems 
               (id, title, platform, url, difficulty, patterns, description)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                prob_id,
                title,
                platform,
                url,
                difficulty,
                json.dumps(patterns if isinstance(patterns, list) else []),
                desc
            )
        )
        conn.commit()
        logger.info(f"Auto-added problem to DB: {prob_id} - {title}")
        return prob_id
    except sqlite3.Error as e:
        logger.error(f"Failed to auto-insert problem {prob_id}: {e}")
        return None
    finally:
        conn.close()


def unified_concept_analysis(
    lecture_id: str,
    problems_discussed: list[dict],
    topics: list[str],
    techniques: list[str],
    all_problems: list[dict],
    course_context: str = "",
    stream_callback: Optional[Callable[[str], None]] = None
) -> dict:
    """Runs a single unified LLM call for problem matching, concept ladders, and MCQs (optimized for speed)."""
    client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_REASONING_API_KEY)
    prompt_template = load_prompt("concept_building.txt")
    
    # Rank candidates by similarity score (tag + text overlap)
    lecture_patterns = list(set(topics + techniques))
    combined_desc = " ".join([p.get("description", "") + " " + p.get("approach", "") for p in problems_discussed if isinstance(p, dict)])
    if not combined_desc:
        combined_desc = " ".join(topics + techniques)
        
    ranked_candidates = find_candidates(combined_desc, lecture_patterns, all_problems, top_k=25)
    
    cands_str = ""
    for idx, p in enumerate(ranked_candidates, 1):
        platform = p.get("platform", "LeetCode")
        diff = p.get("difficulty", "")
        cands_str += f"{idx}. [{platform}] {p['problem_id']} — {p['title']} ({diff})\n"
        cands_str += f"   Patterns: {', '.join(p.get('patterns', []))}\n"
        
    ctx_str = course_context if course_context else f"Lecture ID: {lecture_id}"
    
    prompt = prompt_template.replace("{course_context}", ctx_str)\
                            .replace("{topics}", ", ".join(topics) if isinstance(topics, list) else str(topics))\
                            .replace("{techniques}", ", ".join(techniques) if isinstance(techniques, list) else str(techniques))\
                            .replace("{problems_discussed}", json.dumps(problems_discussed, indent=2))\
                            .replace("{candidates}", cands_str)

    logger.info(f"Running unified concept analysis for {lecture_id}...")
    
    # Model reasoning configuration
    extra_body = None
        
    response_text = ""
    last_exception = None

    for attempt in range(1, 4):
        try:
            try:
                response_stream = client.chat.completions.create(
                    model=LLM_REASONING_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    top_p=LLM_TOP_P,
                    max_tokens=LLM_MAX_TOKENS,
                    extra_body=extra_body,
                    stream=True
                )
                
                chunks = []
                for chunk in response_stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    if delta.content is not None:
                        chunks.append(delta.content)
                        if stream_callback:
                            stream_callback(delta.content)
                            
                response_text = "".join(chunks)
            except Exception as stream_err:
                logger.warning(f"Streaming attempt {attempt} failed ({stream_err}), trying stream=False...")
                try:
                    completion = client.chat.completions.create(
                        model=LLM_REASONING_MODEL,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        top_p=LLM_TOP_P,
                        max_tokens=LLM_MAX_TOKENS,
                        extra_body=extra_body,
                        stream=False
                    )
                except Exception as extra_err:
                    logger.warning(f"Call with extra_body failed ({extra_err}), calling standard model format...")
                    completion = client.chat.completions.create(
                        model=LLM_REASONING_MODEL,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
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
            logger.warning(f"Unified analysis attempt {attempt}/3 failed: {e}")
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

    clean_text = response_text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    elif clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]

    try:
        return json.loads(clean_text.strip())
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse unified analysis JSON for {lecture_id}: {e}\nResponse: {response_text}")
        return {"matches": [], "concept_ladder": [], "mcqs": []}


def process_identification(
    lecture_id: str,
    course_context: str = "",
    stream_callback: Optional[Callable[[str], None]] = None
) -> list[dict]:
    """Full pipeline step 3: loads extraction results, runs unified concept analysis, updates DB."""
    lecture = get_lecture(DB_PATH, lecture_id)
    if not lecture:
        raise ValueError(f"Lecture {lecture_id} not found in DB")
        
    problems_discussed = lecture.get("problems_discussed", [])
    topics = lecture.get("topics", [])
    techniques = lecture.get("techniques", [])
    all_problems = get_all_problems(DB_PATH)
    
    result_data = unified_concept_analysis(
        lecture_id=lecture_id,
        problems_discussed=problems_discussed,
        topics=topics,
        techniques=techniques,
        all_problems=all_problems,
        course_context=course_context,
        stream_callback=stream_callback
    )
    
    matches = result_data.get("matches", [])
    concept_ladder = result_data.get("concept_ladder", [])
    mcqs = result_data.get("mcqs", [])
    
    # Store candidate matches in DB automatically as confirmed=1 and attach to problems_discussed
    for idx, m in enumerate(matches):
        orig_desc = m.get("original_desc", "Lecture problem")
        best_match = m.get("best_match")
        confidence = m.get("confidence", 0.8)
        reasoning = m.get("reasoning", "")
        
        if m.get("no_match_found") and m.get("suggested_new_problem"):
            new_id = auto_insert_discovered_problem(m["suggested_new_problem"], DB_PATH)
            if new_id:
                best_match = new_id
                
        if best_match:
            store_candidates(lecture_id, orig_desc, [{
                "problem_id": best_match,
                "score": confidence,
                "reasoning": reasoning
            }], DB_PATH, confirmed=1)

        if idx < len(problems_discussed) and isinstance(problems_discussed[idx], dict):
            problems_discussed[idx]["matched_problem_id"] = best_match

    # Auto-insert concept ladder problems to DB if missing
    for step in concept_ladder:
        auto_insert_discovered_problem(step, DB_PATH)

    # Update DB record with updated problems_discussed, concept_ladder, mcqs, and current pipeline_hash
    current_hash = compute_pipeline_hash()
    lecture["problems_discussed"] = problems_discussed
    lecture["concept_ladder"] = concept_ladder
    lecture["mcqs"] = mcqs
    lecture["pipeline_hash"] = current_hash
    lecture["status"] = "identified"
    upsert_lecture(DB_PATH, lecture)
    
    return matches
