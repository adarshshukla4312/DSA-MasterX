"""
📅 Dashboard — Today's practice, revision schedule, and progress stats
"""
import streamlit as st
import json
from datetime import date, datetime
from config import DB_PATH
from db.schema import (
    init_db, get_all_lectures, get_all_problems,
    get_attempts, get_solved_problem_ids,
)
from ui_theme import inject_custom_theme

init_db(DB_PATH)
st.set_page_config(page_title="Dashboard", page_icon="📅", layout="wide")
inject_custom_theme()

# ─── Page Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="resend-hero-banner" style="padding: 1.5rem 2rem 1.2rem; margin-bottom: 1.5rem;">
    <div class="badge-pill" style="margin-bottom: 8px;">
        <span class="status-dot"></span>
        <span>Spaced Repetition & Revision • {}</span>
    </div>
    <h1 class="resend-display-xl">📅 Revision Dashboard</h1>
    <p style="color: var(--color-charcoal); font-size: 14px; margin-top: 4px;">Monitor long-term memory retention, SM-2 schedules, and problem mastery.</p>
</div>
""".format(date.today().strftime('%A, %B %d, %Y')), unsafe_allow_html=True)

# ─── Overall Stats Grid ──────────────────────────────────────────────────────
lectures = get_all_lectures(DB_PATH)
problems = get_all_problems(DB_PATH)
all_attempts = get_attempts(DB_PATH)
solved_ids = get_solved_problem_ids(DB_PATH)

total_lectures = len(lectures)
processed = sum(1 for l in lectures if l["status"] != "new")
matched = sum(1 for l in lectures if l["status"] in ("matched", "identified", "completed"))
total_problems = len(problems)
total_solved = len(solved_ids)
total_attempts = len(all_attempts)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="stat-card-v2">
        <div class="stat-number-v2">{processed}/{total_lectures}</div>
        <div class="stat-label-v2">Processed</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card-v2">
        <div class="stat-number-v2">{matched}</div>
        <div class="stat-label-v2">Identified</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card-v2">
        <div class="stat-number-v2">{total_solved}</div>
        <div class="stat-label-v2">Solved</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card-v2">
        <div class="stat-number-v2">{total_attempts}</div>
        <div class="stat-label-v2">Attempts</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    solve_rate = (sum(1 for a in all_attempts if a["solved"]) / total_attempts * 100) if total_attempts > 0 else 0
    st.markdown(f"""
    <div class="stat-card-v2">
        <div class="stat-number-v2">{solve_rate:.0f}%</div>
        <div class="stat-label-v2">Accuracy</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ─── Today's Revision Due ───────────────────────────────────────────────────
st.markdown("### 🔁 Revision Due Today")

try:
    from revision.sm2_scheduler import get_due_reviews, get_revision_stats
    due_reviews = get_due_reviews(DB_PATH)
    rev_stats = get_revision_stats(DB_PATH)

    if due_reviews:
        st.markdown(f"**{len(due_reviews)} patterns** due for review today:")

        for review in due_reviews:
            with st.container(border=True):
                col_info, col_action = st.columns([4, 1])

                with col_info:
                    st.markdown(f"🔁 **Pattern: {review['pattern']}**")
                    if review.get("recommended_problem"):
                        prob = review["recommended_problem"]
                        diff = prob.get("difficulty", "Medium")
                        diff_class = f"diff-{diff.lower()}"
                        st.markdown(
                            f"  → Practice: **{prob.get('title', 'Unknown')}** "
                            f"<span class='{diff_class}'>[{diff}]</span>",
                            unsafe_allow_html=True,
                        )
                        if prob.get("url"):
                            st.markdown(f"  🔗 [{prob.get('platform', 'Link')}]({prob['url']})")
                    st.caption(
                        f"Interval: {review.get('interval', 1):.0f} days • "
                        f"Ease: {review.get('ease_factor', 2.5):.2f} • "
                        f"Reps: {review.get('repetitions', 0)}"
                    )

                with col_action:
                    if review.get("recommended_problem"):
                        if st.button("📊 Log", key=f"rev_log_{review['pattern']}", use_container_width=True):
                            st.session_state[f"rev_logging_{review['pattern']}"] = True

            # Show log form if requested
            if st.session_state.get(f"rev_logging_{review['pattern']}", False) and review.get("recommended_problem"):
                prob = review["recommended_problem"]
                with st.form(f"rev_form_{review['pattern']}"):
                    st.markdown(f"**Log attempt for: {prob.get('title', 'Unknown')}**")
                    col1, col2 = st.columns(2)
                    with col1:
                        solved = st.checkbox("Solved?", value=True, key=f"rev_solved_{review['pattern']}")
                        used_hint = st.checkbox("Used hint?", key=f"rev_hint_{review['pattern']}")
                    with col2:
                        difficulty_felt = st.slider("Difficulty felt", 1, 5, 3, key=f"rev_diff_{review['pattern']}")
                        time_min = st.number_input("Time (min)", 1, 180, 30, key=f"rev_time_{review['pattern']}")

                    if st.form_submit_button("💾 Save", use_container_width=True):
                        from db.schema import log_attempt
                        from revision.sm2_scheduler import update_schedule
                        attempt_data = {
                            "problem_id": prob["id"],
                            "solved": 1 if solved else 0,
                            "difficulty_felt": difficulty_felt,
                            "time_min": time_min,
                            "used_hint": 1 if used_hint else 0,
                            "date": date.today().isoformat(),
                            "notes": "",
                        }
                        log_attempt(DB_PATH, attempt_data)
                        update_schedule(review["pattern"], attempt_data, DB_PATH)
                        st.session_state[f"rev_logging_{review['pattern']}"] = False
                        st.success("Attempt logged & revision schedule updated!")
                        st.rerun()
    else:
        st.success("🎉 No patterns due for review today! Keep solving new problems.")

    # Revision stats
    if rev_stats:
        st.markdown("---")
        st.markdown("### 📈 Revision Stats")
        rcol1, rcol2, rcol3 = st.columns(3)
        with rcol1:
            st.metric("Tracked Patterns", rev_stats.get("total_patterns", 0))
        with rcol2:
            st.metric("Due Today", rev_stats.get("due_today", 0))
        with rcol3:
            st.metric("Mastered (interval > 21d)", rev_stats.get("mastered", 0))

except ImportError:
    st.warning("Revision scheduler not available yet.")
except Exception as e:
    st.warning(f"Could not load revision data: {e}")

st.markdown("---")

# ─── Recent Activity ─────────────────────────────────────────────────────────
st.markdown("### 📊 Recent Activity")

if all_attempts:
    recent = sorted(all_attempts, key=lambda x: x.get("date", ""), reverse=True)[:10]

    for a in recent:
        status = "✅" if a["solved"] else "❌"
        diff_stars = "⭐" * a.get("difficulty_felt", 3)
        hint = " 💡" if a.get("used_hint") else ""

        from db.schema import get_connection
        conn = get_connection(DB_PATH)
        prob = conn.execute("SELECT title FROM problems WHERE id = ?", (a["problem_id"],)).fetchone()
        conn.close()
        prob_title = prob["title"] if prob else a["problem_id"]

        st.markdown(
            f"{status} **{prob_title}** — {a.get('date', 'N/A')} — "
            f"{a.get('time_min', 0)}min — {diff_stars}{hint}"
        )
else:
    st.info("No attempts logged yet. Start solving problems from your practice sheets!")

st.markdown("---")

# ─── Pattern Mastery Heatmap ─────────────────────────────────────────────────
st.markdown("### 🗺️ Pattern Coverage")

if problems:
    pattern_counts = {}
    pattern_solved = {}
    for p in problems:
        patterns = p.get("patterns", [])
        if isinstance(patterns, str):
            try:
                patterns = json.loads(patterns)
            except json.JSONDecodeError:
                patterns = []
        for pat in patterns:
            pattern_counts[pat] = pattern_counts.get(pat, 0) + 1
            if p["id"] in solved_ids:
                pattern_solved[pat] = pattern_solved.get(pat, 0) + 1

    if pattern_counts:
        import pandas as pd
        df = pd.DataFrame([
            {
                "Pattern": pat,
                "Total": count,
                "Solved": pattern_solved.get(pat, 0),
                "Progress": f"{pattern_solved.get(pat, 0)}/{count}",
                "Coverage": pattern_solved.get(pat, 0) / count * 100,
            }
            for pat, count in sorted(pattern_counts.items(), key=lambda x: -x[1])
        ])
        
        st.dataframe(
            df[["Pattern", "Progress", "Coverage"]].style.format({"Coverage": "{:.0f}%"}).background_gradient(
                subset=["Coverage"], cmap="RdYlGn", vmin=0, vmax=100
            ),
            use_container_width=True,
            hide_index=True,
        )
