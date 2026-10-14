import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

with open("benchmark_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for key, m in data["models"].items():
    print("=" * 60)
    print("MODEL:", m["label"])
    print("=" * 60)
    print(f"TTFT: {m['ttft_sec']}s")
    print(f"Total Latency: {m['total_time_sec']}s")
    print(f"Output Chars: {m['output_chars']} (Words: {m['output_words']})")
    print(f"Throughput: {m['tokens_per_sec']} tokens/sec")
    print(f"JSON Valid: {m['json_valid']}")

    pj = m["parsed_json"]
    if not pj:
        print("Parsed JSON is None!")
        continue

    # 1. Matches
    matches = pj.get("matches", [])
    print(f"\n--- Task 1: Problem Matches ({len(matches)} items) ---")
    for i, match in enumerate(matches, 1):
        bm = match.get("best_match")
        conf = match.get("confidence")
        no_m = match.get("no_match_found")
        reason = match.get("reasoning", "")
        print(f"{i}. Best: {bm} | Conf: {conf} | NoMatch: {no_m}")
        print(f"   Reasoning: {reason[:120]}...")
        if no_m:
            sugg = match.get("suggested_new_problem")
            print(f"   Suggested: {sugg}")

    # 2. Concept Ladder
    ladder = pj.get("concept_ladder", [])
    print(f"\n--- Task 2: Concept Ladder ({len(ladder)} steps) ---")
    for s in ladder:
        step = s.get("step")
        pid = s.get("id")
        title = s.get("title")
        diff = s.get("difficulty")
        why = s.get("why_this_problem", "")
        print(f"Step {step}: [{diff}] {pid} - {title}")
        print(f"  Why: {why[:110]}...")

    # 3. MCQs
    mcqs = pj.get("mcqs", [])
    print(f"\n--- Task 3: MCQs ({len(mcqs)} questions) ---")
    l1 = [q for q in mcqs if q.get("level") == 1]
    l2 = [q for q in mcqs if q.get("level") == 2]
    print(f"Level 1 (Recall): {len(l1)} | Level 2 (Reasoning): {len(l2)}")

    invalid_options = [q for q in mcqs if len(q.get("options", [])) != 4]
    invalid_ans = [q for q in mcqs if q.get("answer_idx") not in [0, 1, 2, 3]]
    print(f"Questions with != 4 options: {len(invalid_options)}")
    print(f"Questions with invalid answer_idx: {len(invalid_ans)}")

    # Sample a Level 1 and Level 2 question
    if l1:
        q = l1[0]
        print(f"\nSample Level 1 MCQ:")
        print(f"Q: {q.get('question')}")
        print(f"Opts: {q.get('options')}")
        print(f"Ans: {q.get('answer_idx')} | Expl: {q.get('explanation')[:120]}...")
    if l2:
        q = l2[0]
        print(f"\nSample Level 2 MCQ:")
        print(f"Q: {q.get('question')}")
        print(f"Opts: {q.get('options')}")
        print(f"Ans: {q.get('answer_idx')} | Expl: {q.get('explanation')[:120]}...")
