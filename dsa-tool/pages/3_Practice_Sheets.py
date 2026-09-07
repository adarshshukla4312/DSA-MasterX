"""
📝 Practice Sheets — View generated practice sheets & AI assignments per lecture
"""
import streamlit as st
import json
import urllib.parse
from config import DB_PATH
from db.schema import (
    init_db, get_all_lectures, get_lecture,
    get_confirmed_matches_for_lecture, get_solved_problem_ids,
    log_attempt, get_attempts,
)
from ui_theme import inject_custom_theme

init_db(DB_PATH)
st.set_page_config(page_title="Practice Sheets", page_icon="📝", layout="wide")
inject_custom_theme()


def google_search_url(title: str, platform: str = "LeetCode") -> str:
    """Generate a Google Search URL for a problem title."""
    query = f"{platform} {title}"
    return f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"


def _show_log_form(problem_id: str, title: str):
    """Show the attempt logging form."""
    with st.form(f"attempt_form_{problem_id}"):
        st.markdown(f"**Log attempt for: {title}**")

        col1, col2 = st.columns(2)
        with col1:
            solved = st.checkbox("Solved?", value=True)
            used_hint = st.checkbox("Used hint?", value=False)
        with col2:
            difficulty_felt = st.slider("Difficulty felt", 1, 5, 3, help="1=Very Easy, 5=Very Hard")
            time_min = st.number_input("Time (minutes)", min_value=1, max_value=180, value=30)

        notes = st.text_area("Notes (optional)", placeholder="Any observations, tricks learned...")

        if st.form_submit_button("💾 Save Attempt", use_container_width=True):
            from datetime import date
            attempt_data = {
                "problem_id": problem_id,
                "solved": 1 if solved else 0,
                "difficulty_felt": difficulty_felt,
                "time_min": time_min,
                "used_hint": 1 if used_hint else 0,
                "date": date.today().isoformat(),
                "notes": notes,
            }
            log_attempt(DB_PATH, attempt_data)

            try:
                from revision.sm2_scheduler import update_schedule
                from db.schema import get_connection
                conn = get_connection(DB_PATH)
                row = conn.execute("SELECT patterns FROM problems WHERE id = ?", (problem_id,)).fetchone()
                conn.close()
                if row and row["patterns"]:
                    patterns = json.loads(row["patterns"])
                    for pattern in patterns:
                        update_schedule(pattern, attempt_data, DB_PATH)
            except Exception:
                pass

            st.session_state[f"logging_{problem_id}"] = False
            st.success(f"✅ Attempt logged for {title}!")
            st.rerun()

    prev_attempts = get_attempts(DB_PATH, problem_id)
    if prev_attempts:
        st.caption(f"📊 Previous attempts: {len(prev_attempts)}")
        for a in prev_attempts[:3]:
            status = "✅ Solved" if a["solved"] else "❌ Not solved"
            st.caption(f"  {a['date']} — {status} — {a['time_min']}min — Difficulty: {a['difficulty_felt']}/5")


# ─── Page Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="resend-glow-red" style="padding: 1.5rem 0 1rem; border-bottom: 1px solid var(--color-hairline); margin-bottom: 1.5rem;">
    <div class="badge-pill" style="margin-bottom: 8px;">
        <span class="status-dot"></span>
        <span>Interactive Assignments & MCQs</span>
    </div>
    <h1 class="resend-display-xl">📝 Practice Sheets</h1>
    <p style="color: var(--color-charcoal); font-size: 14px; margin-top: 4px;">Test conceptual understanding, build pattern mastery step-by-step, and practice real LeetCode problems.</p>
</div>
""", unsafe_allow_html=True)

# ─── Get lectures with confirmed matches or extracted status ──────────────────
all_lectures = get_all_lectures(DB_PATH)
matched_lectures = [l for l in all_lectures if l["status"] in ("matched", "extracted", "identified", "completed")]

if not matched_lectures:
    st.info("No practice sheets yet! Process lectures in 📚 Lecture Library.")
    st.stop()

# ─── Lecture selector ─────────────────────────────────────────────────────────
lecture_titles = {l["id"]: l["title"] for l in matched_lectures}
selected_id = st.selectbox(
    "Select a lecture",
    options=list(lecture_titles.keys()),
    format_func=lambda x: lecture_titles[x],
)

lecture = get_lecture(DB_PATH, selected_id)
if not lecture:
    st.error("Lecture not found.")
    st.stop()

st.markdown("---")
solved_ids = get_solved_problem_ids(DB_PATH)

# ─── 0. Pre-Practice Concept Flashcards (Warm-up Recall) ─────────────────────
from pipeline.recommend import synthesize_deterministic_flashcards
flashcards = lecture.get("flashcards") or []
if not flashcards:
    flashcards = synthesize_deterministic_flashcards(lecture)

if flashcards:
    st.markdown("### 🧠 Step 0: Pre-Practice Concept Flashcards (Warm-up Recall)")
    st.caption("Warm up your algorithmic intuition. Test yourself on these high-stress invariants and edge cases before coding.")
    
    with st.expander(f"🔥 View {len(flashcards)} Pre-Practice Flashcards (Click to Reveal Answers)", expanded=True):
        for idx, fc in enumerate(flashcards, 1):
            cat = fc.get("category", "Core Concept")
            stress = fc.get("stress_level", "Essential")
            q_text = fc.get("question", "")
            ans_text = fc.get("answer", "")
            insight = fc.get("core_insight", "")
            snippet = fc.get("code_snippet", "")
            
            with st.container(border=True):
                st.markdown(f"**Card {idx} · `{cat}`** &nbsp; *(Tag: {stress})*")
                st.markdown(f"#### ❓ {q_text}")
                
                show_ans = st.checkbox(f"👁️ Reveal Answer for Card {idx}", key=f"fc_reveal_{selected_id}_{idx}")
                if show_ans:
                    st.success(f"**Verified Solution:**\n\n{ans_text}")
                    if insight:
                        st.info(f"💡 **Key Takeaway:** {insight}")
                    if snippet:
                        st.code(snippet, language="java")

    st.markdown("---")

# ─── 1. Comprehension Verification MCQs (Top of Page) ────────────────────────
mcqs = lecture.get("mcqs", [])
if isinstance(mcqs, list) and mcqs:
    st.markdown("### 📋 Step 1: Two-Level Conceptual Comprehension Check")
    st.caption("Verify your understanding of core concepts and test deep reflection BEFORE writing code.")
    
    # Categorize into Level 1 vs Level 2
    level1_mcqs = [q for q in mcqs if isinstance(q, dict) and q.get("level") == 1]
    level2_mcqs = [q for q in mcqs if isinstance(q, dict) and q.get("level") == 2]
    
    # Backward compatibility for un-leveled MCQs
    if not level1_mcqs and not level2_mcqs:
        mid = max(1, len(mcqs) // 2)
        level1_mcqs = mcqs[:mid]
        level2_mcqs = mcqs[mid:]
        
    def render_mcq_list(q_list: list[dict], level_tag: str):
        for idx, q in enumerate(q_list, 1):
            with st.container(border=True):
                st.markdown(f"**Q{idx}. {q.get('question', '')}**")
                options = q.get("options", [])
                selected_option = st.radio(
                    f"Select answer for Q{idx} ({level_tag})",
                    options=options,
                    key=f"mcq_{selected_id}_{level_tag}_{idx}",
                    index=0,
                    label_visibility="collapsed"
                )
                
                check_key = f"checked_mcq_{selected_id}_{level_tag}_{idx}"
                if st.button(f"Check Answer Q{idx}", key=f"btn_mcq_{selected_id}_{level_tag}_{idx}"):
                    st.session_state[check_key] = True
                    
                if st.session_state.get(check_key, False):
                    correct_idx = q.get("answer_idx", 0)
                    correct_option = options[correct_idx] if correct_idx < len(options) else ""
                    if selected_option == correct_option:
                        st.success(f"✅ Correct! {q.get('explanation', '')}")
                    else:
                        st.error(f"❌ Incorrect. Correct answer: **{correct_option}**\n\n*{q.get('explanation', '')}*")

    tab1, tab2 = st.tabs([
        f"📌 Level 1: Knowledge Retrieval ({len(level1_mcqs)} Questions)",
        f"🧠 Level 2: Critical Reflection & Reasoning ({len(level2_mcqs)} Questions)"
    ])
    
    with tab1:
        st.caption("🎯 **Level 1 Goal:** Direct recall test. If you watched the entire video, you should be able to answer all of these questions.")
        render_mcq_list(level1_mcqs, "l1")
        
    with tab2:
        st.caption("💡 **Level 2 Goal:** Critical questions to challenge your understanding and make you stop, reflect, and think deeply.")
        render_mcq_list(level2_mcqs, "l2")

    st.markdown("<br>", unsafe_allow_html=True)

# ─── 2. Progressive Concept Ladder ──────────────────────────────────────────
ladder = lecture.get("concept_ladder", [])
if isinstance(ladder, list) and ladder:
    st.markdown("### 🪜 Step 2: Progressive Concept Ladder")
    st.caption("A systematically ordered sequence of real LeetCode problems building from warm-up to synthesis.")
    
    for step in ladder:
        prob_id = step.get("id", f"auto-{step.get('title', 'prob').lower().replace(' ', '-')[:30]}")
        title = step.get("title", "Problem")
        diff = step.get("difficulty", "Medium")
        diff_class = f"diff-{diff.lower()}"
        platform = step.get("platform", "LeetCode")
        why = step.get("why_this_problem", "")
        
        search_url = google_search_url(title, platform)
        
        solved = prob_id in solved_ids
        solved_icon = "✅" if solved else "⬜"
        
        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(
                    f"**Step {step.get('step', 1)}:** {solved_icon} **{title}** "
                    f"<span class='{diff_class}'>[{diff}]</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"🔍 [Search on Google → {platform}]({search_url})")
                if why:
                    st.markdown(f"💡 **Why this problem:** *{why}*")
                    
            with col2:
                if st.button("📊 Log", key=f"log_ladder_{selected_id}_{step.get('step', 1)}", use_container_width=True):
                    st.session_state[f"logging_{prob_id}"] = True
                    
        if st.session_state.get(f"logging_{prob_id}", False):
            _show_log_form(prob_id, title)
            
    st.markdown("---")

def render_methodology_checklist_st(scope: str = "global"):
    """Render interactive Systematic DSA Problem-Solving Methodology Checklist."""
    with st.expander("📋 Systematic DSA Problem-Solving Framework", expanded=False):
        st.markdown("""
        > **Core Philosophy:** Mastering DSA is about developing an *intuition-first cognitive workflow*: thoroughly extracting constraints, establishing a solid baseline brute-force, identifying redundant computations, verifying edge cases through pen-and-paper dry runs, and defending complexities rigorously.
        """)

        # Stage 1
        with st.expander("Stage 1: Problem Deconstruction & Constraint Decoupling", expanded=True):
            st.caption("Never jump straight into coding. Interviewers evaluate how rigorously you clarify ambiguity and translate constraints.")
            st.checkbox("Input/Output & Edge Checks: Clarify types, indexing (0 vs 1), empty/null cases, single elements, negative values, duplicates.", key=f"st1_io_{scope}")
            st.checkbox("Map Constraints to Maximum Allowed Time Complexity bound.", key=f"st1_const_{scope}")
            
            st.markdown("##### ⏱️ Constraint-to-Complexity Target Decoder")
            st.markdown("""
            | Constraint Range ($N$) | Target Complexity | Applicable Algorithmic Paradigms |
            | :--- | :--- | :--- |
            | $N \\le 10 - 20$ | $O(2^N)$ or $O(N!)$ | Backtracking, Recursion Trees, Bitmask DP, Permutations / Subsets |
            | $N \\le 100 - 500$ | $O(N^3)$ | Floyd-Warshall, 3D Dynamic Programming, Matrix Multiplications |
            | $N \\le 10^3 - 2,000$ | $O(N^2)$ | 2D DP (LCS, Knapsack), Nested Iterations, All-Pairs Comparisons |
            | $N \\le 10^5 - 10^6$ | $O(N)$ or $O(N \\log N)$ | Sorting, Two Pointers, Sliding Window, Binary Search, Heaps, Hash Maps, BFS/DFS |
            | $N \\ge 10^9$ | $O(\\log N)$ or $O(1)$ | Binary Search on Answer, Mathematical Formulas, Bit Manipulation |
            """)

        # Stage 2
        with st.expander("Stage 2: Formulate the Brute-Force Baseline", expanded=False):
            st.caption("Always articulate the naive solution first before attempting optimizations.")
            st.checkbox("Validates Problem Understanding: Confirms you have grasped core rules correctly.", key=f"st2_val_{scope}")
            st.checkbox("Sets Correctness Anchor: Provides baseline to verify optimizations against.", key=f"st2_anc_{scope}")
            st.checkbox("Prevents Interview Paralysis: Ensures a working approach is communicated out loud.", key=f"st2_par_{scope}")

        # Stage 3
        with st.expander("Stage 3: Spot Redundancy & Optimize Iteratively", expanded=False):
            st.caption("Optimization is the systematic elimination of repeated computations. Ask: 'Where is brute-force wasting time?'")
            st.checkbox("Pinpoint Computational Bottleneck in loops/recalculations.", key=f"st3_bot_{scope}")
            st.checkbox("Apply Canonical Optimization Technique / Data Structure.", key=f"st3_opt_{scope}")

            st.markdown("##### ⚡ Bottleneck-to-Pattern Optimization Matrix")
            st.markdown("""
            | Identified Bottleneck in Brute Force | Optimization Technique / Pattern | Expected Complexity Gain |
            | :--- | :--- | :--- |
            | Repeated linear searches / lookups | Hash Map / Hash Set or Frequency Array | $O(N) \\to O(1)$ average lookup |
            | Recalculating overlapping subproblems | Dynamic Programming (Memoization / Tabulation) | $O(2^N) \\to \\text{Polynomial } O(N \\times K)$ |
            | Searching in ordered / monotonic space | Binary Search (or Binary Search on Answer) | $O(N) \\to O(\\log N)$ |
            | Contiguous subsegments / substrings | Sliding Window (Fixed / Variable) & Prefix Sums | $O(N^2) \\to O(N)$ |
            | Next greater / smaller element queries | Monotonic Stack / Monotonic Queue | $O(N^2) \\to O(N)$ |
            | Continuous dynamic extremes (min / max) | Priority Queue (Min/Max Heap) | $O(N \\log N) \\to O(N \\log K)$ |
            """)

        # Stage 4
        with st.expander("Stage 4: Pen-and-Paper Dry Run (Prior to Coding)", expanded=False):
            st.caption("Catching logic bugs on paper takes seconds; debugging code during an interview takes 20 minutes.")
            st.checkbox("Manual State Tracing: Trace a realistic, non-trivial test case (pointers, accumulators, stacks/queues, visited).", key=f"st4_trc_{scope}")
            st.checkbox("Boundary & Base Conditions: Check termination (left < right vs left <= right), base cases, off-by-one errors.", key=f"st4_bnd_{scope}")
            st.checkbox("Write Structured Pseudocode: Map out helper methods and primary logic blocks before coding.", key=f"st4_pse_{scope}")

        # Stage 5
        with st.expander("Stage 5: Production-Ready Implementation & Complexity Defense", expanded=False):
            st.caption("Write clean, modular code adhering to industry software engineering best practices.")
            st.checkbox("Descriptive Variable Naming: Use windowStart, maxProfit, prevNode instead of single letters.", key=f"st5_nam_{scope}")
            st.checkbox("Defensive Edge Handling: Guard against null pointers, empty collections, integer overflow.", key=f"st5_edg_{scope}")
            st.checkbox("Explicit Complexity Proof: State Best, Average, Worst Time and Auxiliary Space.", key=f"st5_prf_{scope}")

        # Stage 6
        with st.expander("Stage 6: Post-Problem Reflection & Deliberate Practice Rules", expanded=False):
            st.caption("Adhere to these three core deliberate practice rules for interview mastery.")
            st.checkbox("Rule 1: The 30-Minute Struggle Rule (never check solution in first 30-45 mins).", key=f"st6_r1_{scope}")
            st.checkbox("Rule 2: Classify by Canonical Patterns (Two Pointers, Monotonic Stack, Top-K Heaps, etc.).", key=f"st6_r2_{scope}")
            st.checkbox("Rule 3: Active Recall & Spaced Repetition (Zero-to-Hero notes, re-solve 2-3 weeks later).", key=f"st6_r3_{scope}")

        # Bonus
        with st.expander("★ Bonus: The Live Interview Communication Checklist (Think Out Loud)", expanded=False):
            st.caption("Follow this verbal execution checklist during live technical rounds.")
            st.checkbox("Initial 5 Mins: Restate problem in own words, confirm edge cases and constraints before algorithms.", key=f"stb_i5_{scope}")
            st.checkbox("Algorithm Pitch: Propose brute force → state time/space → pitch optimal approach & trade-offs → wait for nod.", key=f"stb_pit_{scope}")
            st.checkbox("During Coding: Narrate each block, avoid long silent pauses, explain data structure choices.", key=f"stb_cod_{scope}")
            st.checkbox("Post Coding: Dry run test case out loud with variable tracking before declaring 'I am done'.", key=f"stb_pst_{scope}")


# ─── 3. Matched Problems (from lecture) ───────────────────────────────────────
confirmed = get_confirmed_matches_for_lecture(DB_PATH, selected_id)

st.markdown("### 🎯 Questions for Practice (Lecture Discussion)")
render_methodology_checklist_st(f"lec_{selected_id}")

if confirmed:
    for match in confirmed:
        patterns = match.get("patterns", [])
        if isinstance(patterns, str):
            try:
                patterns = json.loads(patterns)
            except json.JSONDecodeError:
                patterns = []

        diff = match.get("difficulty", "Medium")
        diff_class = f"diff-{diff.lower()}"
        solved = match["problem_id"] in solved_ids
        solved_icon = "✅" if solved else "⬜"
        
        search_url = google_search_url(match["title"], match.get("platform", "LeetCode"))

        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(
                    f"{solved_icon} **{match['title']}** "
                    f"<span class='{diff_class}'>[{diff}]</span>",
                    unsafe_allow_html=True,
                )
                if isinstance(patterns, list) and patterns:
                    st.markdown(" ".join(f"`{p}`" for p in patterns))
                st.markdown(f"🔍 [Search on Google → {match.get('platform', 'LeetCode')}]({search_url})")
                if match.get("timestamp_start") and match.get("timestamp_end"):
                    st.caption(f"⏱️ Discussed: {match['timestamp_start']} — {match['timestamp_end']}")

            with col2:
                if st.button(
                    "📊 Log",
                    key=f"log_main_{match['problem_id']}",
                    use_container_width=True,
                ):
                    st.session_state[f"logging_{match['problem_id']}"] = True

        if st.session_state.get(f"logging_{match['problem_id']}", False):
            _show_log_form(match["problem_id"], match["title"])
else:
    st.caption("No confirmed database match yet for this lecture. You can generate a custom assignment below!")

st.markdown("---")

# ─── 4. Custom AI Assignment Challenge ──────────────────────────────────────────
st.markdown("### 🧠 Bespoke AI Assignment Challenge")
st.markdown("*Synthesize a brand-new assignment challenge problem for this lecture.*")

challenge_key = f"ai_challenge_{selected_id}"

if st.button("⚡ Generate Custom Assignment Challenge", key=f"btn_gen_{selected_id}"):
    with st.spinner("🧠 DeepSeek V4 Pro is reasoning & designing custom assignment challenge..."):
        from pipeline.recommend import generate_llm_assignment_challenge
        challenge = generate_llm_assignment_challenge(
            lecture_title=lecture.get("title", ""),
            topics=lecture.get("topics", []),
            techniques=lecture.get("techniques", []),
            problems_discussed=lecture.get("problems_discussed", [])
        )
        if challenge:
            st.session_state[challenge_key] = challenge
            st.success("Assignment Challenge Generated!")
        else:
            st.error("Failed to generate challenge. Please try again.")

if challenge_key in st.session_state and st.session_state[challenge_key]:
    c = st.session_state[challenge_key]
    with st.expander(f"📌 {c.get('title', 'Custom Challenge')} [{c.get('difficulty', 'Medium')}]", expanded=True):
        st.markdown(f"**Target Complexity:** `{c.get('target_complexity', 'O(N)')}`")
        st.markdown(f"#### Problem Statement\n{c.get('problem_statement', '')}")
        st.markdown(f"**Input Format:** {c.get('input_format', '')}")
        st.markdown(f"**Output Format:** {c.get('output_format', '')}")
        st.markdown(f"**Constraints:** `{c.get('constraints', '')}`")

        samples = c.get("sample_cases", [])
        if samples:
            st.markdown("#### Sample Test Cases")
            for idx, sc in enumerate(samples, 1):
                st.code(f"Sample Input {idx}:\n{sc.get('input', '')}\n\nSample Output {idx}:\n{sc.get('output', '')}", language="text")
                if sc.get("explanation"):
                    st.caption(f"Explanation: {sc['explanation']}")

        st.markdown("---")
        with st.expander("💡 View Hint"):
            st.info(c.get("hint", "No hint available."))

        with st.expander("🔑 View Solution Strategy"):
            st.success(c.get("solution_strategy", "No strategy provided."))
