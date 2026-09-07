"""
🔍 Identified Problems — Browse all problems discussed in lectures with timestamps & reconstructed code
"""
import streamlit as st
import json
import urllib.parse
from config import DB_PATH
from db.schema import (
    init_db, get_all_lectures, get_lecture,
    get_confirmed_matches_for_lecture, get_solved_problem_ids, get_all_problems
)
from ui_theme import inject_custom_theme

init_db(DB_PATH)
st.set_page_config(page_title="Identified Problems", page_icon="🔍", layout="wide")
inject_custom_theme()


def google_search_url(title: str, platform: str = "LeetCode") -> str:
    """Generate a Google Search URL for a problem title."""
    query = f"{platform} {title}"
    return f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"


def render_methodology_checklist_st(scope: str = "global"):
    """Render interactive Systematic DSA Problem-Solving Methodology Checklist."""
    with st.expander("📋 Systematic DSA Problem-Solving Framework", expanded=False):
        st.markdown("""
        > **Core Philosophy:** Mastering DSA is about developing an *intuition-first cognitive workflow*: thoroughly extracting constraints, establishing a solid baseline brute-force, identifying redundant computations, verifying edge cases through pen-and-paper dry runs, and defending complexities rigorously.
        """)

        # Stage 1
        with st.expander("Stage 1: Problem Deconstruction & Constraint Decoupling", expanded=True):
            st.caption("Never jump straight into coding. Clarify ambiguity and translate constraints into target complexity bounds.")
            st.checkbox("Input/Output & Edge Checks: Clarify types, indexing (0 vs 1), empty/null cases, single elements, negative values, duplicates.", key=f"ip_s1_io_{scope}")
            st.checkbox("Map Constraints to Maximum Allowed Time Complexity bound.", key=f"ip_s1_const_{scope}")
            
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
            st.checkbox("Validates Problem Understanding: Confirms core objectives.", key=f"ip_s2_val_{scope}")
            st.checkbox("Sets Correctness Anchor: Provides baseline to verify optimizations against.", key=f"ip_s2_anc_{scope}")
            st.checkbox("Prevents Interview Paralysis: Ensures a working approach is communicated.", key=f"ip_s2_par_{scope}")

        # Stage 3
        with st.expander("Stage 3: Spot Redundancy & Optimize Iteratively", expanded=False):
            st.caption("Optimization is the systematic elimination of repeated computations.")
            st.checkbox("Pinpoint Computational Bottleneck in loops/recalculations.", key=f"ip_s3_bot_{scope}")
            st.checkbox("Apply Canonical Optimization Technique / Data Structure.", key=f"ip_s3_opt_{scope}")

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
            st.checkbox("Manual State Tracing: Trace a non-trivial test case step-by-step.", key=f"ip_s4_trc_{scope}")
            st.checkbox("Boundary & Base Conditions: Check termination, base cases, off-by-one errors.", key=f"ip_s4_bnd_{scope}")
            st.checkbox("Write Structured Pseudocode: Map out primary logic blocks before coding.", key=f"ip_s4_pse_{scope}")

        # Stage 5
        with st.expander("Stage 5: Production-Ready Implementation & Complexity Defense", expanded=False):
            st.caption("Write clean, modular code adhering to industry software engineering best practices.")
            st.checkbox("Descriptive Variable Naming: Self-documenting variable names.", key=f"ip_s5_nam_{scope}")
            st.checkbox("Defensive Edge Handling: Guard against null pointers, empty collections, integer overflow.", key=f"ip_s5_edg_{scope}")
            st.checkbox("Explicit Complexity Proof: State Best, Average, Worst Time and Space.", key=f"ip_s5_prf_{scope}")

        # Stage 6
        with st.expander("Stage 6: Post-Problem Reflection & Deliberate Practice Rules", expanded=False):
            st.caption("Adhere to these three core deliberate practice rules.")
            st.checkbox("Rule 1: The 30-Minute Struggle Rule (never check solution in first 30-45 mins).", key=f"ip_s6_r1_{scope}")
            st.checkbox("Rule 2: Classify by Canonical Patterns (Two Pointers, Monotonic Stack, etc.).", key=f"ip_s6_r2_{scope}")
            st.checkbox("Rule 3: Active Recall & Spaced Repetition (Zero-to-Hero notes, re-solve 2-3 weeks later).", key=f"ip_s6_r3_{scope}")

        # Bonus
        with st.expander("★ Bonus: The Live Interview Communication Checklist (Think Out Loud)", expanded=False):
            st.caption("Follow this verbal execution checklist during live technical rounds.")
            st.checkbox("Initial 5 Mins: Restate problem, confirm edge cases and constraints before algorithms.", key=f"ip_stb_i5_{scope}")
            st.checkbox("Algorithm Pitch: Propose brute force → pitch optimal approach & trade-offs → wait for nod.", key=f"ip_stb_pit_{scope}")
            st.checkbox("During Coding: Narrate each block, avoid long silences, explain data structure choices.", key=f"ip_stb_cod_{scope}")
            st.checkbox("Post Coding: Dry run test case out loud with variable tracking before declaring 'I am done'.", key=f"ip_stb_pst_{scope}")



# ─── Page Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="resend-glow-green" style="padding: 1.5rem 0 1rem; border-bottom: 1px solid var(--color-hairline); margin-bottom: 1.5rem;">
    <div class="badge-pill" style="margin-bottom: 8px;">
        <span class="status-dot"></span>
        <span>Reconstructed Code & Timestamps</span>
    </div>
    <h1 class="resend-display-xl">🔍 Identified Problems</h1>
    <p style="color: var(--color-charcoal); font-size: 14px; margin-top: 4px;">Browse extracted problems, verbal code reconstructions, and exact video timestamps.</p>
</div>
""", unsafe_allow_html=True)

all_lectures = get_all_lectures(DB_PATH)
processed_lectures = [l for l in all_lectures if l["status"] in ("extracted", "identified", "matched", "completed")]

if not processed_lectures:
    st.info("No identified problems yet! Process your lecture videos in 📚 Lecture Library.")
    st.stop()

# ─── Search & Filter Controls ────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])
with col1:
    search_query = st.text_input("🔍 Search problems by keyword or concept", placeholder="e.g. prefix sum, subarray, binary search...")
with col2:
    selected_lecture = st.selectbox(
        "Filter by Lecture",
        options=["All Lectures"] + [f"{l['id']} — {l['title']}" for l in processed_lectures]
    )

st.markdown("---")

# ─── Display Extracted & Matched Problems ────────────────────────────────────
db_problems_map = {p["id"]: p for p in get_all_problems(DB_PATH)}
solved_ids = get_solved_problem_ids(DB_PATH)

total_found = 0

for lec in processed_lectures:
    lec_label = f"{lec['id']} — {lec['title']}"
    if selected_lecture != "All Lectures" and selected_lecture != lec_label:
        continue
        
    problems_discussed = lec.get("problems_discussed", [])
    matches = get_confirmed_matches_for_lecture(DB_PATH, lec["id"])
    matches_by_id = {m["problem_id"]: m for m in matches}
    
    if not problems_discussed and not matches:
        continue
        
    total_found += len(problems_discussed) if problems_discussed else len(matches)

    with st.expander(f"📖 {lec['title']} ({lec['filename']})", expanded=True):
        render_methodology_checklist_st(lec["id"])
        if problems_discussed:
            for idx, prob in enumerate(problems_discussed, 1):
                if isinstance(prob, str):
                    st.markdown(f"**Problem {idx}:** {prob}")
                    continue
                    
                desc = prob.get("description", "Problem discussed in lecture")
                
                # Filter check
                if search_query and search_query.lower() not in desc.lower() and search_query.lower() not in prob.get("approach", "").lower():
                    continue
                    
                approach = prob.get("approach", "")
                trick = prob.get("core_trick", "")
                code = prob.get("code_reconstruction", "")
                ts = prob.get("timestamp_range", [])
                
                st.markdown(f"### Problem {idx}: {desc}")
                
                if isinstance(ts, list) and len(ts) == 2:
                    st.markdown(f"<span class='status-pill status-extracted'>⏱️ {ts[0]} — {ts[1]}</span>", unsafe_allow_html=True)
                    
                st.markdown("<br>", unsafe_allow_html=True)
                
                cols = st.columns(2)
                if approach:
                    cols[0].markdown(f"🔧 **Approach:** {approach}")
                if trick:
                    cols[1].markdown(f"💡 **Core Trick:** {trick}")
                    
                if code:
                    st.markdown("**Verbal Code Reconstruction (as taught in class):**")
                    st.code(code, language="java")
                    
                # Display matched famous online problem with Google search link
                matching_p = None
                matched_id = prob.get("matched_problem_id") if isinstance(prob, dict) else None
                if matched_id and matched_id in db_problems_map:
                    matching_p = db_problems_map[matched_id]
                elif idx - 1 < len(matches):
                    matching_p = matches[idx - 1]

                if not matching_p:
                    # Fallback 1: Check lecture_problem_matches DB table
                    from db.schema import get_connection
                    conn = get_connection(DB_PATH)
                    row = conn.execute(
                        "SELECT problem_id FROM lecture_problem_matches WHERE lecture_id = ? ORDER BY confirmed DESC, match_score DESC LIMIT 1 OFFSET ?",
                        (lec["id"], idx - 1)
                    ).fetchone()
                    conn.close()
                    if row and row["problem_id"] in db_problems_map:
                        matching_p = db_problems_map[row["problem_id"]]

                if not matching_p and isinstance(prob, dict):
                    # Fallback 2: On-the-fly similarity match against problem database
                    from pipeline.match_db import find_candidates
                    p_desc = prob.get("description", "") + " " + prob.get("approach", "")
                    p_patterns = lec.get("topics", []) + lec.get("techniques", [])
                    cands = find_candidates(p_desc, p_patterns, list(db_problems_map.values()), top_k=1)
                    if cands and cands[0]["score"] > 0.05:
                        matching_p = db_problems_map.get(cands[0]["problem_id"])

                if matching_p:
                    diff = matching_p.get("difficulty", "Medium")
                    diff_class = f"diff-{diff.lower()}"
                    platform = matching_p.get("platform", "LeetCode")
                    search_url = google_search_url(matching_p["title"], platform)
                    st.markdown(
                        f"🔍 **Matched Problem:** [{matching_p['title']}]({search_url}) "
                        f"<span class='{diff_class}'>[{diff}]</span>",
                        unsafe_allow_html=True
                    )
                st.divider()
        else:
            st.caption("No individual problem segments extracted for this lecture.")

if total_found == 0:
    st.info("No problems match your search filter.")
