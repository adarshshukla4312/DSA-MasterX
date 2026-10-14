"""
GritX — Main Streamlit App (Resend Design System)
"""
import streamlit as st
from pathlib import Path

# Must be the first Streamlit command
st.set_page_config(
    page_title="GritX",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from config import DB_PATH, PROBLEMS_JSON, get_hardware_status
from db.schema import init_db, load_problems_from_json
from ui_theme import inject_custom_theme

# ─── Initialize DB & Theme ───────────────────────────────────────────────────
init_db(DB_PATH)
inject_custom_theme()


@st.cache_resource
def _seed_problems():
    if PROBLEMS_JSON.exists():
        count = load_problems_from_json(DB_PATH, PROBLEMS_JSON)
        return count
    return 0


_seed_problems()

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
        <span class="status-dot"></span>
        <span style="font-family: var(--font-serif); font-size: 1.8rem; color: var(--color-ink);">resend / dsa</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Hardware Status Badge
    hw = get_hardware_status()
    st.markdown(f"""
    <div class="badge-pill" style="margin-bottom: 16px; width: 100%;">
        <span>⚡ {hw["label"]}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='border-color: var(--color-hairline); margin: 16px 0;'>", unsafe_allow_html=True)
    st.markdown("""
    **Workflow Navigation:**
    1. 📚 **Lecture Library** — Scan & process
    2. 🔍 **Identified Problems** — View code & timestamps
    3. 📝 **Practice Sheets** — MCQs & Concept Ladders
    4. 📅 **Dashboard** — SM-2 Spaced repetition
    """)
    st.markdown("<hr style='border-color: var(--color-hairline); margin: 16px 0;'>", unsafe_allow_html=True)
    
    from db.schema import get_all_lectures, get_all_problems, get_attempts
    lectures = get_all_lectures(DB_PATH)
    problems = get_all_problems(DB_PATH)
    attempts = get_attempts(DB_PATH)
    
    col1, col2 = st.columns(2)
    with col1:
        processed = sum(1 for l in lectures if l["status"] != "new")
        st.metric("Processed", f"{processed}/{len(lectures)}")
    with col2:
        st.metric("Problems", len(problems))
    
    col3, col4 = st.columns(2)
    with col3:
        solved = len({a["problem_id"] for a in attempts if a["solved"]})
        st.metric("Solved", solved)
    with col4:
        st.metric("Attempts", len(attempts))

# ─── Main Hero Banner (Resend Orange Glow + Domaine Display Typography) ───────
st.markdown("""
<div class="resend-hero-banner">
    <div class="badge-pill" style="margin-bottom: 16px;">
        <span class="status-dot"></span>
        <span>Local GPU & Reasoner Active</span>
    </div>
    <h1 class="resend-display-xxl" style="margin-bottom: 12px;">
        GritX
    </h1>
    <p style="color: var(--color-body); font-family: var(--font-sans-marketing); font-size: 1.1rem; max-width: 820px; margin: 0; line-height: 1.6;">
        Transform offline lecture videos into interactive practice ladders, verbal code reconstructions, and AI-driven assignments powered by local GPU transcription and reasoning.
    </p>
</div>
""", unsafe_allow_html=True)

# ─── Stats Grid (Resend Stat Cards) ──────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stat-card-v2">
        <div class="stat-number-v2">{len(lectures)}</div>
        <div class="stat-label-v2">Total Lectures</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card-v2">
        <div class="stat-number-v2">{len(problems)}</div>
        <div class="stat-label-v2">Problem Database</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card-v2">
        <div class="stat-number-v2">{solved}</div>
        <div class="stat-label-v2">Problems Solved</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    identified_cnt = sum(1 for l in lectures if l["status"] in ("identified", "matched"))
    st.markdown(f"""
    <div class="stat-card-v2">
        <div class="stat-number-v2">{identified_cnt}</div>
        <div class="stat-label-v2">Identified Lectures</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border-color: var(--color-hairline); margin: 32px 0;'>", unsafe_allow_html=True)

# ─── Interactive Workflow Timeline ─────────────────────────────────────────
st.markdown("<h2 class='resend-display-xl' style='font-size: 32px; margin-bottom: 24px;'>Workflow Architecture</h2>", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    with st.container():
        st.markdown("""
        <div class="glass-card">
            <div class="badge-pill" style="margin-bottom: 8px;">Step 1</div>
            <h4 style="margin: 4px 0 8px; color: var(--color-ink);">📚 Scan & Process</h4>
            <p style="color: var(--color-charcoal); font-size: 13px; line-height: 1.5; margin: 0;">GPU extracts audio, runs Whisper, and streams DeepSeek V4 reasoning in real time.</p>
        </div>
        """, unsafe_allow_html=True)

with c2:
    with st.container():
        st.markdown("""
        <div class="glass-card">
            <div class="badge-pill" style="margin-bottom: 8px;">Step 2</div>
            <h4 style="margin: 4px 0 8px; color: var(--color-ink);">🔍 Identified Code</h4>
            <p style="color: var(--color-charcoal); font-size: 13px; line-height: 1.5; margin: 0;">View verbal code reconstructions, exact timestamps, and automatic LeetCode links.</p>
        </div>
        """, unsafe_allow_html=True)

with c3:
    with st.container():
        st.markdown("""
        <div class="glass-card">
            <div class="badge-pill" style="margin-bottom: 8px;">Step 3</div>
            <h4 style="margin: 4px 0 8px; color: var(--color-ink);">📝 Practice Sheets</h4>
            <p style="color: var(--color-charcoal); font-size: 13px; line-height: 1.5; margin: 0;">Test understanding with interactive MCQs and practice step-by-step problem ladders.</p>
        </div>
        """, unsafe_allow_html=True)

with c4:
    with st.container():
        st.markdown("""
        <div class="glass-card">
            <div class="badge-pill" style="margin-bottom: 8px;">Step 4</div>
            <h4 style="margin: 4px 0 8px; color: var(--color-ink);">📅 SM-2 Spaced Review</h4>
            <p style="color: var(--color-charcoal); font-size: 13px; line-height: 1.5; margin: 0;">Algorithmically schedules pattern review to guarantee long-term retention.</p>
        </div>
        """, unsafe_allow_html=True)
