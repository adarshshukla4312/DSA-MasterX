import os
import sys
import time
import json
from pathlib import Path
from openai import OpenAI

sys.stdout.reconfigure(encoding="utf-8")

from config import (
    DB_PATH,
    LLM_BASE_URL,
    LLM_REASONING_API_KEY,
    LLM_REASONING_MODEL,
    LLM_STANDARD_API_KEY,
    LLM_STANDARD_MODEL,
    LLM_TOP_P,
    LLM_MAX_TOKENS,
)
from db.schema import get_lecture, get_all_problems
from pipeline.match_db import find_candidates
from pipeline.extract_concepts import load_prompt

def build_prompt(lecture_id="47-advanced-dsa-arrays-3"):
    lecture = get_lecture(DB_PATH, lecture_id)
    if not lecture:
        raise ValueError(f"Lecture {lecture_id} not found")
        
    problems_discussed = lecture.get("problems_discussed", [])
    topics = lecture.get("topics", [])
    techniques = lecture.get("techniques", [])
    all_problems = get_all_problems(DB_PATH)
    
    prompt_template = load_prompt("concept_building.txt")
    lecture_patterns = list(set(topics + techniques))
    
    combined_desc = ""
    for p in problems_discussed:
        if not isinstance(p, dict):
            continue
        combined_desc += p.get("description", "") + " "
        combined_desc += p.get("approach", "") + " "
        for appr in p.get("approaches", []):
            if isinstance(appr, dict):
                combined_desc += appr.get("name", "") + " "
                combined_desc += " ".join(appr.get("steps", [])) + " "
    if not combined_desc.strip():
        combined_desc = " ".join(topics + techniques)
        
    ranked_candidates = find_candidates(combined_desc, lecture_patterns, all_problems, top_k=25)
    
    cands_str = ""
    for idx, p in enumerate(ranked_candidates, 1):
        platform = p.get("platform", "LeetCode")
        diff = p.get("difficulty", "")
        cands_str += f"{idx}. [{platform}] {p['problem_id']} — {p['title']} ({diff})\n"
        cands_str += f"   Patterns: {', '.join(p.get('patterns', []))}\n"
        
    ctx_str = f"Lecture ID: {lecture_id}"
    prompt = prompt_template.replace("{course_context}", ctx_str)\
                            .replace("{topics}", ", ".join(topics) if isinstance(topics, list) else str(topics))\
                            .replace("{techniques}", ", ".join(techniques) if isinstance(techniques, list) else str(techniques))\
                            .replace("{problems_discussed}", json.dumps(problems_discussed, indent=2))\
                            .replace("{candidates}", cands_str)
                            
    return prompt, problems_discussed

def run_model_benchmark(model_name, api_key, prompt, label):
    print(f"\n==========================================")
    print(f"Starting Benchmark: {label}")
    print(f"Model: {model_name}")
    print(f"==========================================")
    
    client = OpenAI(base_url=LLM_BASE_URL, api_key=api_key)
    
    start_time = time.perf_counter()
    first_token_time = None
    chunks = []
    
    try:
        response_stream = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            top_p=LLM_TOP_P,
            max_tokens=LLM_MAX_TOKENS,
            stream=True
        )
        
        for chunk in response_stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = delta.content
            if content:
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                    print(f"[{label}] First token received in {first_token_time - start_time:.2f}s")
                chunks.append(content)
                
        total_time = time.perf_counter() - start_time
        ttft = (first_token_time - start_time) if first_token_time else total_time
        full_text = "".join(chunks)
        
    except Exception as e:
        print(f"[{label}] Streaming error: {e}. Trying non-streaming fallback...")
        start_time = time.perf_counter()
        resp = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            top_p=LLM_TOP_P,
            max_tokens=LLM_MAX_TOKENS,
            stream=False
        )
        total_time = time.perf_counter() - start_time
        ttft = total_time
        full_text = resp.choices[0].message.content or ""
        
    clean_text = full_text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    elif clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()
    
    parsed_json = None
    parse_error = None
    try:
        parsed_json = json.loads(clean_text)
    except Exception as e:
        parse_error = str(e)
        
    output_chars = len(full_text)
    output_words = len(full_text.split())
    approx_tokens = int(output_chars / 4)
    tokens_per_sec = (approx_tokens / total_time) if total_time > 0 else 0
    
    print(f"[{label}] Finished in {total_time:.2f}s (TTFT: {ttft:.2f}s, Chars: {output_chars}, Words: {output_words}, Approx Tokens/s: {tokens_per_sec:.1f})")
    print(f"[{label}] JSON Parsed Successfully: {parsed_json is not None}")
    if parse_error:
        print(f"[{label}] JSON Parse Error: {parse_error}")
        
    return {
        "label": label,
        "model": model_name,
        "ttft_sec": round(ttft, 2),
        "total_time_sec": round(total_time, 2),
        "output_chars": output_chars,
        "output_words": output_words,
        "approx_tokens": approx_tokens,
        "tokens_per_sec": round(tokens_per_sec, 1),
        "json_valid": parsed_json is not None,
        "parse_error": parse_error,
        "raw_response": full_text,
        "parsed_json": parsed_json
    }

def main():
    print("Building prompt for 47-advanced-dsa-arrays-3...")
    prompt, problems_discussed = build_prompt("47-advanced-dsa-arrays-3")
    print(f"Prompt prepared ({len(prompt)} chars, {len(problems_discussed)} problems discussed in lecture).")
    
    # 1. Run Current Step 3 Model (Nemotron 3 Ultra 550b)
    res_nemotron = run_model_benchmark(
        model_name=LLM_REASONING_MODEL,
        api_key=LLM_REASONING_API_KEY,
        prompt=prompt,
        label="Current Step 3 (Nemotron 3 Ultra 550B)"
    )
    
    # Pause slightly between runs to avoid rate-limiting
    time.sleep(3)
    
    # 2. Run DeepSeek 4.1 (deepseek-v4.1-flash)
    res_deepseek = run_model_benchmark(
        model_name=LLM_STANDARD_MODEL,
        api_key=LLM_STANDARD_API_KEY,
        prompt=prompt,
        label="DeepSeek 4.1 (deepseek-v4.1-flash)"
    )
    
    # Save results to benchmark_results.json
    results = {
        "lecture_id": "47-advanced-dsa-arrays-3",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "models": {
            "current_step3": res_nemotron,
            "deepseek_4_1": res_deepseek
        }
    }
    
    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("\nBenchmark complete! Results saved to benchmark_results.json.")

if __name__ == "__main__":
    main()
