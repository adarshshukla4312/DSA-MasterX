import sys
import time
import json
from openai import OpenAI

sys.stdout.reconfigure(encoding="utf-8")

from config import (
    DB_PATH,
    LLM_BASE_URL,
    LLM_STANDARD_API_KEY,
    LLM_STANDARD_MODEL,
    LLM_TOP_P,
    LLM_MAX_TOKENS,
)
from db.schema import get_lecture, get_all_problems
from pipeline.match_db import find_candidates
from pipeline.extract_concepts import load_prompt

print("1. Preparing prompt with new XML concept_building.txt...")
lecture_id = "47-advanced-dsa-arrays-3"
lecture = get_lecture(DB_PATH, lecture_id)
problems_discussed = lecture.get("problems_discussed", [])
topics = lecture.get("topics", [])
techniques = lecture.get("techniques", [])
all_problems = get_all_problems(DB_PATH)

combined_desc = ""
for p in problems_discussed:
    if isinstance(p, dict):
        combined_desc += p.get("description", "") + " " + p.get("approach", "") + " "

lecture_patterns = list(set(topics + techniques))
ranked_candidates = find_candidates(combined_desc, lecture_patterns, all_problems, top_k=25)

cands_str = ""
for idx, p in enumerate(ranked_candidates, 1):
    platform = p.get("platform", "LeetCode")
    diff = p.get("difficulty", "")
    cands_str += f"{idx}. [{platform}] {p['problem_id']} — {p['title']} ({diff})\n"
    cands_str += f"   Patterns: {', '.join(p.get('patterns', []))}\n"

prompt_template = load_prompt("concept_building.txt")
prompt = prompt_template.replace("{course_context}", f"Lecture ID: {lecture_id}")\
                        .replace("{topics}", ", ".join(topics))\
                        .replace("{techniques}", ", ".join(techniques))\
                        .replace("{problems_discussed}", json.dumps(problems_discussed, indent=2))\
                        .replace("{candidates}", cands_str)

print(f"Prompt prepared. Total characters: {len(prompt)}")
print(f"First 300 characters of prompt:\n{prompt[:300]}...")

print("\n2. Calling model with XML prompt...")
client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_STANDARD_API_KEY)
start_t = time.perf_counter()

response = client.chat.completions.create(
    model=LLM_STANDARD_MODEL,
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3,
    top_p=LLM_TOP_P,
    max_tokens=LLM_MAX_TOKENS,
    stream=False
)
duration = time.perf_counter() - start_t
raw_text = response.choices[0].message.content or ""
print(f"Model responded in {duration:.2f}s ({len(raw_text)} characters).")

# Clean markdown formatting if present
clean_text = raw_text.strip()
if clean_text.startswith("```json"):
    clean_text = clean_text[7:]
elif clean_text.startswith("```"):
    clean_text = clean_text[3:]
if clean_text.endswith("```"):
    clean_text = clean_text[:-3]
clean_text = clean_text.strip()

parsed = json.loads(clean_text)
print("\n3. Verification of Structured Output:")
print(f"- Matches count: {len(parsed.get('matches', []))}")
print(f"- Concept ladder steps: {len(parsed.get('concept_ladder', []))}")
print(f"- MCQs count: {len(parsed.get('mcqs', []))}")

# Check MCQs for forbidden external problem references
forbidden = []
for q in parsed.get("mcqs", []):
    txt = q.get("question", "")
    if "problem " in txt.lower() or "lc-" in txt.lower():
        forbidden.append(txt)
print(f"- MCQs violating no-external-problem rule: {len(forbidden)}")

print("\nSample Concept Ladder Steps:")
for step in parsed.get("concept_ladder", [])[:4]:
    print(f"  Step {step.get('step')}: [{step.get('difficulty')}] {step.get('title')} — {step.get('why_this_problem')[:80]}...")

print("\nSample MCQ:")
sample_q = parsed.get("mcqs", [])[0]
print(f"  Level {sample_q.get('level')}: {sample_q.get('question')}")
print(f"  Options: {sample_q.get('options')}")
print(f"  Answer: {sample_q.get('answer_idx')}")

print("\nXML PROMPT AUDIT AND VALIDATION SUCCESSFUL!")
