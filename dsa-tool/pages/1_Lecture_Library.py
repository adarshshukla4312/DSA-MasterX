"""
📚 Lecture Library — Browse, scan, and process lecture videos
"""
import streamlit as st
import json
import logging
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="Lecture Library", page_icon="📚", layout="wide")

from config import DB_PATH, LECTURE_DIR, VIDEO_EXTENSIONS, LOG_FILE_PATH, get_hardware_status
from db.schema import init_db, get_all_lectures, upsert_lecture, get_lecture
from pipeline.pipeline_version import compute_pipeline_hash
from ui_theme import inject_custom_theme

init_db(DB_PATH)
inject_custom_theme()
logger = logging.getLogger(__name__)


def read_recent_logs(max_lines: int = 35) -> str:
    """Read the last max_lines from dsa_tool.log."""
    if not LOG_FILE_PATH.exists():
        return "Log file not created yet."
    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return "".join(lines[-max_lines:])
    except Exception as e:
        return f"Could not read log file: {e}"


# ─── Sidebar Hardware Status ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🧠 DSA Mastery")
    hw = get_hardware_status()
    st.info(hw["label"])
    st.markdown("---")
    st.markdown(f"**Current Pipeline Hash:** `{compute_pipeline_hash()[:8]}`")


def build_course_context(all_videos: list[dict], current_video: dict) -> str:
    """Generates scope-bounded course context using the full 113-lecture curriculum."""
    from curriculum import build_llm_course_context
    curr_num = current_video.get("num", "0")
    try:
        num = int(curr_num)
    except (ValueError, TypeError):
        num = 0
    if num > 0:
        return build_llm_course_context(num)
    # Fallback for unnumbered videos
    return f"Lecture: {current_video.get('title', 'Unknown')}"


# ─── Processing Pipeline Handler ──────────────────────────────────────────────
def run_processing_pipeline(video_info: dict, all_videos: list[dict], skip_transcription: bool = False):
    """Executes processing pipeline via a background thread independent of Streamlit UI browser tabs."""
    import time
    from pipeline.runner import start_background_job, get_job_status, cancel_job

    lecture_id = video_info["lecture_id"]
    title = video_info["title"]
    course_context = build_course_context(all_videos, video_info)

    # Start background job if not already active or completed/cancelled
    start_background_job(
        lecture_id,
        skip_transcription=skip_transcription,
        course_context=course_context,
        force_restart=False
    )

    st.markdown(f"## ⚙️ Background Processing Dashboard")
    st.info("🔒 **Background Worker Active:** Processing runs in an independent Python thread on your machine. You can safely switch tabs, minimize, refresh, or close Chrome — processing will NOT stop!")

    st.markdown(f"**Target Lecture:** `{title}` (`{video_info['filename']}`)")
    st.caption(f"📍 **Course Context:** {course_context.splitlines()[0] if course_context else 'None'}")

    status_area = st.empty()
    progress_bar = st.progress(0)

    log_expander = st.expander("📜 Live Background Worker Logs", expanded=True)
    log_area = log_expander.empty()

    job_status = get_job_status(lecture_id)
    status = job_status.get("status", "processing")
    progress = job_status.get("progress", 0)
    step_name = job_status.get("step_name", "Processing")
    logs = job_status.get("logs", [])
    err = job_status.get("error")

    progress_bar.progress(min(max(progress, 0), 100))
    status_area.markdown(f"### ⚙️ {step_name} ({progress}%)")

    if logs:
        log_area.code("\n".join(logs[-25:]), language="text")
    else:
        log_area.caption("Initializing worker logs...")

    if status in ("processing", "starting", "cancelling"):
        if status == "cancelling":
            st.warning("🛑 Stopping pipeline processing... Please wait for worker thread to exit cleanly.")
        else:
            if st.button("🛑 Stop / Cancel Processing"):
                cancel_job(lecture_id)
                st.warning("🛑 Stop request sent to background worker...")
                time.sleep(0.5)
                st.rerun()

        time.sleep(1.5)
        st.rerun()

    elif status == "completed":
        progress_bar.progress(100)
        status_area.markdown("### 🎉 Processing Complete!")
        st.success("Lecture concept analysis, practice ladder, and MCQs generated successfully!")

        # Check if there is a queue to process
        process_queue = st.session_state.get("process_queue", [])
        if process_queue and process_queue[0].get("lecture_id") == lecture_id:
            process_queue.pop(0)
            st.session_state["process_queue"] = process_queue
            if process_queue:
                next_video = process_queue[0]
                st.session_state["processing_video_info"] = next_video
                start_background_job(
                    next_video["lecture_id"],
                    skip_transcription=False,
                    course_context=build_course_context(all_videos, next_video),
                    force_restart=True
                )
                st.rerun()
            else:
                st.session_state.pop("process_queue", None)

        col_done, _ = st.columns([2, 5])
        with col_done:
            if st.button("▶️ Continue to Library", use_container_width=True):
                st.session_state.pop("processing_video_info", None)
                st.session_state.pop("skip_transcription", None)
                st.rerun()

    elif status in ("cancelled", "error"):
        progress_bar.empty()
        # Clear batch queue on cancellation or error
        st.session_state.pop("process_queue", None)

        if status == "cancelled":
            st.warning("🛑 Processing was stopped by user.")
        else:
            st.error(f"❌ Background Processing Error: {err}")

        col_dismiss, _ = st.columns([2, 5])
        with col_dismiss:
            if st.button("↩️ Dismiss", use_container_width=True):
                st.session_state.pop("processing_video_info", None)
                st.session_state.pop("skip_transcription", None)
                st.rerun()


# ─── Helper Functions ───────────────────────────────────────────────────────
def _extract_video_sort_key(file_path: Path) -> tuple[int, str]:
    name = file_path.stem
    parts = name.split(".", 1)
    if len(parts) >= 2 and parts[0].strip().isdigit():
        return (int(parts[0].strip()), name)
    m = re.match(r'^(?:L|Lecture)?\s*(\d+)', name, re.IGNORECASE)
    if m:
        return (int(m.group(1)), name)
    return (999999, name)


def scan_videos(lecture_dir: Path) -> list[dict]:
    """Scan directory for video files and return metadata."""
    videos = []
    if not lecture_dir or not lecture_dir.exists():
        return videos

    ignore_dirs = {
        "transcript", "transcripts", "dsa-tool", "data", "audio", "db", "frontend",
        "pages", "pipeline", "prompts", "revision", "scratch", "scripts", "__pycache__",
        ".git", ".venv", "venv", "env", "node_modules", ".gemini", ".idea", ".vscode"
    }

    seen_ids = set()
    all_files = []

    for root, dirs, files in os.walk(lecture_dir):
        dirs[:] = [d for d in dirs if d.lower() not in ignore_dirs and not d.startswith(".")]
        for file in files:
            f = Path(root) / file
            if f.suffix.lower() in VIDEO_EXTENSIONS:
                all_files.append(f)

    all_files.sort(key=_extract_video_sort_key)

    for f in all_files:
        name = f.stem
        parts = name.split(".", 1)
        if len(parts) == 2 and parts[0].strip().isdigit():
            num = parts[0].strip()
            title = parts[1].strip().lstrip("_ ")
        else:
            m = re.match(r'^(?:L|Lecture)?\s*(\d+)', name, re.IGNORECASE)
            num = m.group(1) if m else ""
            title = name

        lecture_id = name.lower().replace(" ", "-").replace("_", "-")
        lecture_id = "".join(c for c in lecture_id if c.isalnum() or c == "-")
        lecture_id = "-".join(p for p in lecture_id.split("-") if p)[:60]

        if lecture_id in seen_ids:
            continue
        seen_ids.add(lecture_id)

        videos.append({
            "filename": f.name,
            "title": title,
            "video_path": str(f),
            "lecture_id": lecture_id,
            "num": num,
            "size_mb": f.stat().st_size / (1024 * 1024),
        })
    return videos


def get_status_badge(status: str) -> str:
    """Return HTML badge for lecture status following Resend status dot specs."""
    badges = {
        "new": '<span class="status-pill status-new"><span class="status-dot" style="background-color: var(--color-accent-orange);"></span> New</span>',
        "transcribed": '<span class="status-pill status-transcribed"><span class="status-dot" style="background-color: var(--color-accent-yellow);"></span> Transcribed</span>',
        "extracted": '<span class="status-pill status-extracted"><span class="status-dot" style="background-color: var(--color-accent-blue);"></span> Extracted</span>',
        "identified": '<span class="status-pill status-identified"><span class="status-dot"></span> Identified</span>',
        "matched": '<span class="status-pill status-identified"><span class="status-dot"></span> Matched</span>',
    }
    return badges.get(status, badges["new"])


# ─── Page Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="resend-glow-blue" style="padding: 1.5rem 0 1rem; border-bottom: 1px solid var(--color-hairline); margin-bottom: 1.5rem;">
    <div class="badge-pill" style="margin-bottom: 8px;">
        <span class="status-dot"></span>
        <span>Lecture Processing Pipeline</span>
    </div>
    <h1 class="resend-display-xl">📚 Lecture Library</h1>
    <p style="color: var(--color-charcoal); font-size: 14px; margin-top: 4px;">Local Video Source: <code>{}</code></p>
</div>
""".format(LECTURE_DIR), unsafe_allow_html=True)

videos = scan_videos(LECTURE_DIR)
current_pipeline_hash = compute_pipeline_hash()

# ─── Full-Width Active Processing Dashboard ─────────────────────────────────
if "processing_video_info" in st.session_state:
    skip_trans = st.session_state.get("skip_transcription", False)
    with st.container(border=True):
        run_processing_pipeline(
            st.session_state["processing_video_info"],
            videos,
            skip_transcription=skip_trans
        )
    st.markdown("---")

# ─── Scan & Sync DB ─────────────────────────────────────────────────────────
db_lectures = {l["id"]: l for l in get_all_lectures(DB_PATH)}
for v in videos:
    lid = v["lecture_id"]
    if lid not in db_lectures:
        upsert_lecture(DB_PATH, {
            "id": lid,
            "title": v["title"],
            "filename": v["filename"],
            "video_path": v["video_path"],
            "transcript_path": "",
            "topics": [],
            "techniques": [],
            "difficulty": "",
            "key_moments": [],
            "problems_discussed": [],
            "concept_ladder": [],
            "mcqs": [],
            "pipeline_hash": "",
            "status": "new",
            "processed_at": None,
        })
        db_lectures[lid] = {"status": "new", "pipeline_hash": ""}
    else:
        existing = db_lectures[lid]
        if existing.get("video_path") != v["video_path"] or existing.get("filename") != v["filename"]:
            existing["video_path"] = v["video_path"]
            existing["filename"] = v["filename"]
            upsert_lecture(DB_PATH, existing)

# ─── Filter Controls & Process All Queue Button ──────────────────────────────
col1, col2, col3, col4 = st.columns([2, 1, 1, 1.2])
with col1:
    search = st.text_input("🔍 Search lectures", placeholder="e.g., Arrays, Recursion, Bit...")
with col2:
    status_filter = st.selectbox("Status", ["All", "New", "Transcribed", "Extracted", "Identified/Matched"])
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Rescan Directory", use_container_width=True):
        st.rerun()
with col4:
    st.markdown("<br>", unsafe_allow_html=True)
    unprocessed = [v for v in videos if db_lectures.get(v["lecture_id"], {}).get("status") == "new"]
    if st.button(f"▶️ Process All ({len(unprocessed)})", use_container_width=True, disabled=len(unprocessed) == 0):
        st.session_state["process_queue"] = unprocessed
        if unprocessed:
            st.session_state["processing_video_info"] = unprocessed[0]
            from pipeline.runner import start_background_job
            start_background_job(
                unprocessed[0]["lecture_id"],
                skip_transcription=False,
                course_context=build_course_context(videos, unprocessed[0]),
                force_restart=True
            )
            st.rerun()

st.markdown("---")

# ─── Filter Videos ───────────────────────────────────────────────────────────
filtered = videos
if search:
    search_lower = search.lower()
    filtered = [v for v in filtered if search_lower in v["title"].lower() or search_lower in v["filename"].lower()]
if status_filter != "All":
    if status_filter == "Identified/Matched":
        filtered = [v for v in filtered if db_lectures.get(v["lecture_id"], {}).get("status") in ("identified", "matched")]
    else:
        status_val = status_filter.lower()
        filtered = [v for v in filtered if db_lectures.get(v["lecture_id"], {}).get("status", "new") == status_val]

st.markdown(f"**Showing {len(filtered)} of {len(videos)} lectures**")

# ─── Lecture Cards ───────────────────────────────────────────────────────────
for v in filtered:
    lec_record = db_lectures.get(v["lecture_id"], {})
    status = lec_record.get("status", "new")
    stored_hash = lec_record.get("pipeline_hash", "")
    is_outdated = (status in ("extracted", "identified", "matched")) and stored_hash and (stored_hash != current_pipeline_hash)

    lecture_data = get_lecture(DB_PATH, v["lecture_id"])

    with st.container(border=True):
        col_info, col_status, col_action = st.columns([4.2, 1.3, 1.5])

        with col_info:
            num_str = f"**Lecture {v['num']}** — " if v.get('num') else ""
            st.markdown(f"{num_str}**{v['title']}**")
            st.caption(f"📁 `{v['filename']}`  •  💾 {v['size_mb']:.0f} MB")

            if lecture_data and lecture_data.get("topics"):
                topics = lecture_data["topics"]
                if isinstance(topics, list) and topics:
                    tags = " ".join(f"`{t}`" for t in topics[:5])
                    st.markdown(tags)

        with col_status:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(get_status_badge(status), unsafe_allow_html=True)
            if is_outdated:
                st.markdown('<span class="status-pill status-outdated">⚠️ Pipeline Updated</span>', unsafe_allow_html=True)

        with col_action:
            st.markdown("<br>", unsafe_allow_html=True)
            from pipeline.runner import start_background_job
            if status == "new":
                if st.button("▶️ Process", key=f"process_{v['lecture_id']}", use_container_width=True):
                    st.session_state["processing_video_info"] = v
                    st.session_state["skip_transcription"] = False
                    start_background_job(
                        v["lecture_id"],
                        skip_transcription=False,
                        course_context=build_course_context(videos, v),
                        force_restart=True
                    )
                    st.rerun()
            elif is_outdated:
                if st.button("🔄 Re-process", key=f"reprocess_{v['lecture_id']}", use_container_width=True, help="Prompts or pipeline updated! Re-run LLM analysis without re-transcribing audio."):
                    st.session_state["processing_video_info"] = v
                    st.session_state["skip_transcription"] = True
                    start_background_job(
                        v["lecture_id"],
                        skip_transcription=True,
                        course_context=build_course_context(videos, v),
                        force_restart=True
                    )
                    st.rerun()
            elif status == "transcribed":
                if st.button("🧠 Extract", key=f"extract_{v['lecture_id']}", use_container_width=True):
                    st.session_state["processing_video_info"] = v
                    st.session_state["skip_transcription"] = True
                    start_background_job(
                        v["lecture_id"],
                        skip_transcription=True,
                        course_context=build_course_context(videos, v),
                        force_restart=True
                    )
                    st.rerun()
            else:
                if st.button("🔄 Re-run Analysis", key=f"rerun_{v['lecture_id']}", use_container_width=True):
                    st.session_state["processing_video_info"] = v
                    st.session_state["skip_transcription"] = True
                    start_background_job(
                        v["lecture_id"],
                        skip_transcription=True,
                        course_context=build_course_context(videos, v),
                        force_restart=True
                    )
                    st.rerun()

st.markdown("---")

# ─── Live Log Viewer ────────────────────────────────────────────────────────
with st.expander("📜 Live System & Process Logs", expanded=False):
    st.caption(f"Log file path: `{LOG_FILE_PATH}`")
    if st.button("🔄 Refresh Logs"):
        st.rerun()
    st.code(read_recent_logs(40), language="text")
