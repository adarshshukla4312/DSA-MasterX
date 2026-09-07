import json
import logging
from pathlib import Path

from config import (
    DB_PATH,
    RECOMMEND_EASY,
    RECOMMEND_MEDIUM,
    RECOMMEND_HARD,
    LLM_REASONING_API_KEY,
    LLM_REASONING_MODEL,
    LLM_BASE_URL,
    LLM_TOP_P,
    LLM_MAX_TOKENS,
    LLM_THINKING
)
from db.schema import (
    get_lecture,
    get_all_problems,
    get_solved_problem_ids,
    get_confirmed_matches_for_lecture
)
from pipeline.extract_concepts import get_llm_client

logger = logging.getLogger(__name__)

def recommend_problems(patterns: list[str], solved_ids: set[str], db_path: str | Path) -> list[dict]:
    """Finds problems matching patterns, excludes solved, orders by difficulty."""
    all_problems = get_all_problems(db_path)
    
    candidates = []
    pattern_set = set(p.lower() for p in patterns)
    
    for prob in all_problems:
        if prob["id"] in solved_ids:
            continue
            
        prob_patterns = set(p.lower() for p in prob.get("patterns", []))
        if pattern_set.intersection(prob_patterns):
            candidates.append(prob)
            
    easy_probs = [p for p in candidates if p.get("difficulty", "Medium").lower() == "easy"]
    medium_probs = [p for p in candidates if p.get("difficulty", "Medium").lower() == "medium"]
    hard_probs = [p for p in candidates if p.get("difficulty", "Medium").lower() == "hard"]
    
    recommended = []
    recommended.extend(easy_probs[:RECOMMEND_EASY])
    recommended.extend(medium_probs[:RECOMMEND_MEDIUM])
    recommended.extend(hard_probs[:RECOMMEND_HARD])
    
    return recommended

def generate_llm_assignment_challenge(lecture_title: str, topics: list[str], techniques: list[str], problems_discussed: list[dict]) -> dict | None:
    """Uses the Reasoning model to create a custom assignment challenge problem tailored to the lecture."""
    from openai import OpenAI
    client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_REASONING_API_KEY)
    
    prompt = f"""You are a senior DSA curriculum designer.
Analyze the following lecture details and generate a brand-new, customized coding assignment challenge problem designed to test mastery of the lecture's core techniques.

Lecture Title: {lecture_title}
Topics Covered: {', '.join(topics) if isinstance(topics, list) else topics}
Techniques: {', '.join(techniques) if isinstance(techniques, list) else techniques}
Problems Discussed: {json.dumps(problems_discussed, indent=2)}

Create a comprehensive assignment challenge with:
1. Title
2. Difficulty (Easy / Medium / Hard)
3. Problem Statement (Whiteboard / Interview style)
4. Input & Output Specification
5. Constraints (e.g. N <= 10^5)
6. Sample Input & Sample Output with Explanation
7. Target Time & Space Complexity (e.g. O(N) time, O(1) space)
8. Hint (hidden trick)
9. Optimal Solution Strategy

Respond with ONLY valid JSON in this structure:
```json
{{
  "title": "Custom Challenge Title",
  "difficulty": "Medium",
  "problem_statement": "Detailed problem statement...",
  "input_format": "Input description",
  "output_format": "Output description",
  "constraints": "N <= 10^5",
  "sample_cases": [
    {{"input": "[1, 2, 3]", "output": "6", "explanation": "..."}}
  ],
  "target_complexity": "Time: O(N), Space: O(1)",
  "hint": "Think about prefix sum...",
  "solution_strategy": "High level optimal approach..."
}}
```
"""
    extra_body = {"chat_template_kwargs": {"enable_thinking": True}, "reasoning_budget": 16384}
    last_exception = None

    for attempt in range(1, 4):
        try:
            completion = client.chat.completions.create(
                model=LLM_REASONING_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                top_p=LLM_TOP_P,
                max_tokens=LLM_MAX_TOKENS,
                extra_body=extra_body,
                stream=False
            )
            
            response_text = completion.choices[0].message.content.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
                
            return json.loads(response_text.strip())
        except Exception as e:
            last_exception = e
            logger.warning(f"Assignment challenge generation attempt {attempt}/3 failed: {e}")
            if attempt < 3:
                import time
                time.sleep(2 * attempt)
def synthesize_deterministic_flashcards(lecture: dict) -> list[dict]:
    """Generates 4-5 high-yield, pre-practice warm-up flashcards from lecture extracted concepts."""
    title = lecture.get("title", "DSA Lecture")
    topics = lecture.get("topics", [])
    techniques = lecture.get("techniques", [])
    problems = lecture.get("problems_discussed", [])
    mcqs = lecture.get("mcqs", [])
    moments = lecture.get("key_moments", [])
    
    flashcards = []
    
    # 1. Primary Algorithmic Invariant & Core Intuition
    primary_technique = techniques[0] if techniques else (topics[0] if topics else "the primary algorithm")
    p1 = problems[0] if problems and isinstance(problems[0], dict) else {}
    p1_desc = p1.get("description", f"the core problem in {title}")
    p1_trick = p1.get("core_trick", "") or p1.get("approach", "") or f"Mastering {primary_technique} requires decoupling invariants from edge bounds."
    p1_ts = p1.get("timestamp_range", ["00:00", ""])[0] if isinstance(p1.get("timestamp_range"), list) else "00:00"

    flashcards.append({
        "id": "fc-1",
        "question": f"What is the foundational intuition and core invariant behind {primary_technique}?",
        "answer": p1_trick,
        "core_insight": f"Always anchor understanding on {primary_technique} before exploring boundary optimizations.",
        "category": "Core Concept",
        "stress_level": "Essential",
        "code_snippet": p1.get("code_reconstruction", "")[:280] if p1.get("code_reconstruction") else "",
        "timestamp": p1_ts
    })

    # 2. Critical Edge Case & High-Stress Pitfall
    edge_cases = []
    if "prefix sum" in primary_technique.lower() or "array" in primary_technique.lower():
        edge_cases.append("Range queries with L = 0 require special boundary handling (or 1-indexed prefix array of size N+1) to avoid negative index out-of-bounds.")
    if "recursion" in primary_technique.lower() or "tree" in primary_technique.lower():
        edge_cases.append("Missing or improperly ordered base cases cause StackOverflowError; always verify single-element and null/empty node guards.")
    if "two pointer" in primary_technique.lower() or "binary search" in primary_technique.lower():
        edge_cases.append("Loop termination condition (left < right vs left <= right) and midpoint overflow `mid = left + (right - left) / 2`.")
    if not edge_cases:
        edge_cases.append("Empty/null collections, single-element arrays, negative elements, integer overflow during accumulation, and duplicate elements.")

    flashcards.append({
        "id": "fc-2",
        "question": f"What subtle edge cases or boundary conditions are most frequently missed in {primary_technique}?",
        "answer": " ".join(edge_cases),
        "core_insight": "Catching boundary bugs during interview problem deconstruction prevents critical runtime faults.",
        "category": "Edge Case & Pitfall",
        "stress_level": "Common Trap",
        "code_snippet": "// Defensive guard:\nif (arr == null || arr.length == 0) return 0;\n// Avoid integer overflow:\nlong currentSum = 0;",
        "timestamp": p1_ts
    })

    # 3. Complexity Trade-Off & Defense
    p1_approach = p1.get("approach", "")
    time_space_info = "Time Complexity: O(N) or O(N log N) depending on sorting/traversal; Auxiliary Space: O(1) in-place or O(N) when allocating secondary buffers."
    if "O(" in p1_approach:
        time_space_info = p1_approach
    elif "prefix" in primary_technique.lower():
        time_space_info = "Precomputation Time: O(N), Query Time: O(1). Auxiliary Space: O(N) for prefix table or O(1) if mutated in-place."
    elif "tree" in primary_technique.lower():
        time_space_info = "Time Complexity: O(N) since each node is visited once. Auxiliary Space: O(H) where H is tree height (O(log N) balanced, O(N) skewed) for call stack."

    flashcards.append({
        "id": "fc-3",
        "question": f"What are the target Time and Auxiliary Space complexities for {p1_desc[:90]}...?",
        "answer": time_space_info,
        "core_insight": "Always distinguish input memory from auxiliary recursion stack / heap allocations when defending complexities.",
        "category": "Complexity Defense",
        "stress_level": "Interview Invariant",
        "code_snippet": "",
        "timestamp": p1_ts
    })

    # 4. Secondary Problem Hook or Optimization Technique
    if len(problems) > 1 and isinstance(problems[1], dict):
        p2 = problems[1]
        p2_desc = p2.get("description", "Secondary algorithmic pattern")
        p2_trick = p2.get("core_trick", "") or p2.get("approach", "Optimize repeated operations by maintaining running state.")
        p2_ts = p2.get("timestamp_range", ["", ""])[0] if isinstance(p2.get("timestamp_range"), list) else ""

        flashcards.append({
            "id": "fc-4",
            "question": f"For problem '{p2_desc[:90]}', what is the key optimization that beats the brute-force baseline?",
            "answer": p2_trick,
            "core_insight": "Identify the computational bottleneck in nested loops to unlock linear or logarithmic gains.",
            "category": "Optimization Hook",
            "stress_level": "High Yield",
            "code_snippet": p2.get("code_reconstruction", "")[:280] if p2.get("code_reconstruction") else "",
            "timestamp": p2_ts
        })
    else:
        sec_tech = techniques[1] if len(techniques) > 1 else "State Tracking"
        flashcards.append({
            "id": "fc-4",
            "question": f"How can redundant computations be systematically eliminated when applying {sec_tech}?",
            "answer": "Maintain rolling state (hash map, two pointers, prefix sums, or sliding window) to convert repeated linear searches from O(N) to O(1) amortized.",
            "core_insight": "Store previously computed results to eliminate redundant iterations.",
            "category": "Optimization Hook",
            "stress_level": "High Yield",
            "code_snippet": "",
            "timestamp": moments[0].get("timestamp", "00:00") if moments else "00:00"
        })

    # 5. Critical Reflection / What-If Scenario
    l2_mcq = next((m for m in mcqs if isinstance(m, dict) and m.get("level") == 2), None)
    if l2_mcq:
        q_text = l2_mcq.get("question", "")
        correct_idx = l2_mcq.get("answer_idx", 0)
        options = l2_mcq.get("options", [])
        correct_opt = options[correct_idx] if correct_idx < len(options) else ""
        expl = l2_mcq.get("explanation", correct_opt)

        flashcards.append({
            "id": "fc-5",
            "question": f"Critical Reflection: {q_text}",
            "answer": f"**Correct Solution:** {correct_opt}\n\n{expl}",
            "core_insight": "Critical edge cases distinguish strong candidates in technical rounds.",
            "category": "Critical Reflection",
            "stress_level": "High Trap",
            "code_snippet": "",
            "timestamp": moments[-1].get("timestamp", "") if moments else ""
        })
    else:
        flashcards.append({
            "id": "fc-5",
            "question": f"What happens if input constraints include negative values or large elements up to 10^9 in {primary_technique}?",
            "answer": "Negative values may invalidate greedy monotonicity assumptions (e.g. standard sliding window), requiring prefix sums with HashMaps instead. Large sums require 64-bit `long` to prevent silent integer overflow.",
            "core_insight": "Always check whether input constraints permit negative numbers before picking variable-window sliding window.",
            "category": "Critical Reflection",
            "stress_level": "High Trap",
            "code_snippet": "",
            "timestamp": ""
        })

    return flashcards


def generate_llm_flashcards(
    lecture_title: str,
    topics: list[str],
    techniques: list[str],
    problems_discussed: list[dict],
    key_moments: list[dict]
) -> list[dict] | None:
    """Uses LLM to generate 4-5 bespoke high-stress interview recall flashcards."""
    from openai import OpenAI
    client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_REASONING_API_KEY)

    prompt = f"""You are a master technical interview coach and DSA curriculum architect.
Analyze the following lecture details and generate exactly 5 high-yield, pre-practice recall flashcards.
Focus specifically on concepts that candidates frequently forget, subtle traps, boundary edge cases, time/space trade-offs, and critical invariants stressed in the lecture.

Lecture Title: {lecture_title}
Topics: {', '.join(topics) if isinstance(topics, list) else topics}
Techniques: {', '.join(techniques) if isinstance(techniques, list) else techniques}
Problems Discussed: {json.dumps(problems_discussed, indent=2)}
Key Moments: {json.dumps(key_moments, indent=2)}

Create exactly 5 flashcards covering:
1. Core Technique & Foundational Invariant
2. High-Stress Boundary Condition & Common Trap (e.g. 0-index vs 1-index, overflow, empty case)
3. Asymptotic Complexity Proof & Space Trade-off
4. Key Algorithmic Optimization Hook (how brute-force bottleneck is eliminated)
5. Critical Reflection / What-If Scenario (e.g. negative numbers, duplicates, skewed trees)

Output ONLY valid JSON as an array of 5 flashcard objects with this exact structure:
```json
[
  {{
    "id": "fc-1",
    "question": "Clear, thought-provoking question or interview scenario...",
    "answer": "Concise, highly precise explanation with direct solution...",
    "core_insight": "One-line golden rule / takeaway...",
    "category": "Core Concept", // or "Edge Case & Pitfall", "Complexity Defense", "Optimization Hook", "Critical Reflection"
    "stress_level": "Essential", // or "Common Trap", "Interview Invariant", "High Yield", "High Trap"
    "code_snippet": "// Optional concise Java snippet or formula if applicable",
    "timestamp": "MM:SS"
  }}
]
```
"""
    extra_body = {"chat_template_kwargs": {"enable_thinking": True}, "reasoning_budget": 8192}

    for attempt in range(1, 4):
        try:
            completion = client.chat.completions.create(
                model=LLM_REASONING_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                top_p=LLM_TOP_P,
                max_tokens=LLM_MAX_TOKENS,
                extra_body=extra_body,
                stream=False
            )
            response_text = completion.choices[0].message.content.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            parsed = json.loads(response_text.strip())
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed
        except Exception as e:
            logger.warning(f"LLM flashcard generation attempt {attempt}/3 failed: {e}")
            if attempt < 3:
                import time
                time.sleep(2 * attempt)

    return None


def get_practice_sheet(lecture_id: str) -> dict:
    """Given a lecture with confirmed matches, generates a practice sheet including LLM custom assignment challenge."""
    lecture = get_lecture(DB_PATH, lecture_id)
    if not lecture:
        raise ValueError(f"Lecture {lecture_id} not found in DB")
        
    confirmed_matches = get_confirmed_matches_for_lecture(DB_PATH, lecture_id)
    
    all_patterns = set()
    for match in confirmed_matches:
        for p in match.get("patterns", []):
            all_patterns.add(p)
            
    for t in lecture.get("techniques", []):
        all_patterns.add(t)
        
    solved_ids = get_solved_problem_ids(DB_PATH)
    recommended = recommend_problems(list(all_patterns), solved_ids, DB_PATH)
    
    # Load or synthesize flashcards
    flashcards = lecture.get("flashcards") or []
    if not flashcards:
        flashcards = synthesize_deterministic_flashcards(lecture)

    return {
        "lecture_id": lecture_id,
        "lecture_title": lecture.get("title", ""),
        "topics": lecture.get("topics", []),
        "techniques": lecture.get("techniques", []),
        "matched_problems": confirmed_matches,
        "recommended_problems": recommended,
        "total_recommended": len(recommended),
        "flashcards": flashcards
    }

