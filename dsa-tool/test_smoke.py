"""Quick smoke test for all modules."""
import sys

# Test 1: Config
from config import LECTURE_DIR, DB_PATH, LLM_STANDARD_MODEL, LLM_REASONING_MODEL
print(f"[OK] Config loaded. LECTURE_DIR={LECTURE_DIR}, STANDARD_MODEL={LLM_STANDARD_MODEL}, REASONING_MODEL={LLM_REASONING_MODEL}")

# Test 2: DB
from db.schema import init_db, get_all_problems
init_db(DB_PATH)
problems = get_all_problems(DB_PATH)
print(f"[OK] DB works. {len(problems)} problems in database")

# Test 3: Pipeline imports
from pipeline.transcribe import scan_lectures
videos = scan_lectures(LECTURE_DIR)
print(f"[OK] Transcribe module. Found {len(videos)} video files")

from pipeline.extract_concepts import get_llm_client, load_prompt
prompt = load_prompt("concept_extraction.txt")
print(f"[OK] Extract concepts module. Prompt loaded ({len(prompt)} chars)")

from pipeline.match_db import find_candidates, compute_tag_overlap
score = compute_tag_overlap(["Array", "HashMap"], ["Array", "DP"])
print(f"[OK] Match DB module. Tag overlap test: {score:.2f}")

from pipeline.recommend import get_practice_sheet
print("[OK] Recommend module loaded")

from pipeline.identify_problem import process_identification
print("[OK] Identify problem module loaded")

# Test 4: SM-2
from revision.sm2_scheduler import calculate_sm2, map_attempt_to_quality
new_reps, new_ef, new_interval = calculate_sm2(4, 0, 2.5, 0)
print(f"[OK] SM-2 scheduler. quality=4 -> reps={new_reps}, ef={new_ef:.2f}, interval={new_interval:.1f}")

print("\n[PASS] All modules loaded successfully!")
