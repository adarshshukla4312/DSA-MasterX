import os
import sys
import re
import json
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
import datetime
import webbrowser
import threading
import time
import socket

# Imports from existing modules
import config
from config import (
    DB_PATH, PROBLEMS_JSON, LOG_FILE_PATH, get_hardware_status, VIDEO_EXTENSIONS, update_lecture_dir
)
from db.schema import (
    init_db, load_problems_from_json, get_lecture, get_all_lectures,
    upsert_lecture, get_all_problems, get_solved_problem_ids,
    get_confirmed_matches_for_lecture, log_attempt, get_attempts, get_connection
)
from revision.sm2_scheduler import get_due_reviews, get_revision_stats, update_schedule
from pipeline.runner import get_job_status, cancel_job, start_background_job, ACTIVE_JOBS, _jobs_lock
from pipeline.recommend import (
    get_practice_sheet, generate_llm_assignment_challenge,
    synthesize_deterministic_flashcards, generate_llm_flashcards
)
from pipeline.pipeline_version import compute_pipeline_hash
from curriculum import build_llm_course_context

app = FastAPI(title="DSA Mastery Tool API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_no_cache_header(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Startup logic
@app.on_event("startup")
def on_startup():
    init_db(DB_PATH)
    if PROBLEMS_JSON.exists():
        load_problems_from_json(DB_PATH, PROBLEMS_JSON)

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
    """Scan directory for video files and return metadata in numerical order."""
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
            "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
        })
    return videos

# Endpoints

# --- Lectures ---

def _get_lecture_sort_key(item: dict) -> tuple[int, str]:
    num = item.get("num")
    if num is not None and str(num).strip().isdigit():
        return (int(str(num).strip()), item.get("title", ""))
    filename = item.get("filename", "")
    m = re.match(r'^(\d+)', filename)
    if m:
        return (int(m.group(1)), filename)
    id_str = item.get("id", "")
    m2 = re.match(r'^(\d+)', id_str)
    if m2:
        return (int(m2.group(1)), id_str)
    return (999999, filename or id_str)

@app.get("/api/lectures")
def api_get_lectures():
    lectures_db = get_all_lectures(DB_PATH)
    db_map = {l["id"]: l for l in lectures_db}
    
    videos = scan_videos(config.LECTURE_DIR)
    
    results = []
    for v in videos:
        lid = v["lecture_id"]
        rec = db_map.get(lid, {})
        merged = {
            **rec,
            **v,
            "id": lid,
        }
        if not merged.get("status"):
            merged["status"] = rec.get("status", "new")
        with _jobs_lock:
            if lid in ACTIVE_JOBS:
                merged["status"] = ACTIVE_JOBS[lid].get("status", "processing")
        results.append(merged)
        
    results.sort(key=_get_lecture_sort_key)
    return results

@app.get("/api/lectures/{lecture_id}")
def api_get_lecture(lecture_id: str):
    rec = get_lecture(DB_PATH, lecture_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Lecture not found")
    return rec

@app.post("/api/lectures/scan")
def api_scan_lectures():
    videos = scan_videos(config.LECTURE_DIR)
    db_lectures = {l["id"]: l for l in get_all_lectures(DB_PATH)}
    
    new_count = 0
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
            new_count += 1
        else:
            existing = db_lectures[lid]
            if existing.get("video_path") != v["video_path"] or existing.get("filename") != v["filename"]:
                existing["video_path"] = v["video_path"]
                existing["filename"] = v["filename"]
                upsert_lecture(DB_PATH, existing)
            
    return {"scanned": len(videos), "new": new_count}

class ProcessRequest(BaseModel):
    skip_transcription: bool = False

def build_course_context_helper(current_video: dict) -> str:
    curr_num = current_video.get("num", "0")
    try:
        num = int(curr_num)
    except (ValueError, TypeError):
        num = 0
    if num > 0:
        return build_llm_course_context(num)
    return f"Lecture: {current_video.get('title', 'Unknown')}"

@app.post("/api/lectures/{lecture_id}/process")
def api_process_lecture(lecture_id: str, req: ProcessRequest = ProcessRequest()):
    videos = scan_videos(config.LECTURE_DIR)
    video_info = next((v for v in videos if v["lecture_id"] == lecture_id), None)
    
    if not video_info:
        # Fallback to DB info if not in video dir
        rec = get_lecture(DB_PATH, lecture_id)
        if not rec:
            raise HTTPException(status_code=404, detail="Lecture not found")
        video_info = rec
        video_info["num"] = 0
    else:
        rec = get_lecture(DB_PATH, lecture_id)
        if rec and rec.get("video_path") != video_info["video_path"]:
            rec["video_path"] = video_info["video_path"]
            upsert_lecture(DB_PATH, rec)
        
    course_context = build_course_context_helper(video_info)
    
    th = start_background_job(
        lecture_id,
        skip_transcription=req.skip_transcription,
        course_context=course_context,
        force_restart=False
    )
    if th is None:
        return {"status": "already_running"}
    return {"status": "started"}

@app.get("/api/lectures/{lecture_id}/job")
def api_get_job_status(lecture_id: str):
    return get_job_status(lecture_id)

@app.post("/api/lectures/{lecture_id}/cancel")
def api_cancel_job(lecture_id: str):
    cancelled = cancel_job(lecture_id)
    return {"cancelled": cancelled}

@app.post("/api/lectures/process-all")
def api_process_all():
    with _jobs_lock:
        for lid, j in ACTIVE_JOBS.items():
            if j.get("status") in ("processing", "starting"):
                return {"queued": 0, "started": lid, "message": "A job is already currently running."}

    lectures = get_all_lectures(DB_PATH)
    unprocessed = [l for l in lectures if l.get("status") == "new"]
    if not unprocessed:
        return {"queued": 0, "started": None}
    
    first = unprocessed[0]
    videos = scan_videos(config.LECTURE_DIR)
    video_info = next((v for v in videos if v["lecture_id"] == first["id"]), first)
    
    course_context = build_course_context_helper(video_info)
    
    start_background_job(
        first["id"],
        skip_transcription=False,
        course_context=course_context,
        force_restart=False
    )
    
    return {"queued": len(unprocessed), "started": first["id"]}


# --- Problems & Matches ---

@app.get("/api/problems")
def api_get_problems():
    return get_all_problems(DB_PATH)

@app.get("/api/problems/solved")
def api_get_solved_problems():
    solved_ids = get_solved_problem_ids(DB_PATH)
    return {"solved_ids": list(solved_ids)}

@app.get("/api/lectures/{lecture_id}/matches")
def api_get_lecture_matches(lecture_id: str):
    return get_confirmed_matches_for_lecture(DB_PATH, lecture_id)


# --- Practice & Attempts ---

@app.get("/api/lectures/{lecture_id}/practice")
def api_get_practice(lecture_id: str):
    try:
        return get_practice_sheet(lecture_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/lectures/{lecture_id}/challenge")
def api_challenge(lecture_id: str):
    lecture = get_lecture(DB_PATH, lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
    challenge = generate_llm_assignment_challenge(
        lecture.get("title", ""),
        lecture.get("topics", []),
        lecture.get("techniques", []),
        lecture.get("problems_discussed", [])
    )
@app.get("/api/lectures/{lecture_id}/flashcards")
def api_get_flashcards(lecture_id: str):
    lecture = get_lecture(DB_PATH, lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
    
    flashcards = lecture.get("flashcards") or []
    if not flashcards:
        flashcards = synthesize_deterministic_flashcards(lecture)
        
    return {"lecture_id": lecture_id, "flashcards": flashcards}

@app.post("/api/lectures/{lecture_id}/flashcards/generate")
def api_generate_flashcards(lecture_id: str):
    lecture = get_lecture(DB_PATH, lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
        
    generated = generate_llm_flashcards(
        lecture.get("title", ""),
        lecture.get("topics", []),
        lecture.get("techniques", []),
        lecture.get("problems_discussed", []),
        lecture.get("key_moments", [])
    )
    
    if not generated:
        # Fallback to deterministic synthesis if LLM fails
        generated = synthesize_deterministic_flashcards(lecture)
        
    lecture["flashcards"] = generated
    upsert_lecture(DB_PATH, lecture)
    
    return {"status": "generated", "flashcards": generated}

class AttemptRequest(BaseModel):
    problem_id: str
    solved: bool
    difficulty_felt: int
    time_min: int
    used_hint: bool
    notes: str = ""

@app.post("/api/attempts")
def api_log_attempt(req: AttemptRequest):
    now_iso = datetime.datetime.now().isoformat()
    
    # 1. Ensure problem exists in problems table to satisfy FK constraint
    conn = get_connection(DB_PATH)
    with conn:
        row = conn.execute("SELECT id FROM problems WHERE id = ?", (req.problem_id,)).fetchone()
        if not row:
            conn.execute(
                """INSERT OR IGNORE INTO problems (id, title, platform, difficulty, patterns, description)
                   VALUES (?, ?, 'Custom', 'Medium', '[]', '')""",
                (req.problem_id, req.problem_id)
            )
    conn.close()
    
    # 2. Log attempt
    attempt_data = {
        "problem_id": req.problem_id,
        "solved": 1 if req.solved else 0,
        "difficulty_felt": req.difficulty_felt,
        "time_min": req.time_min,
        "used_hint": 1 if req.used_hint else 0,
        "date": now_iso,
        "notes": req.notes
    }
    
    log_attempt(DB_PATH, attempt_data)
    
    # 3. Update SM-2 schedule for patterns
    problems = get_all_problems(DB_PATH)
    prob = next((p for p in problems if p["id"] == req.problem_id), None)
    if prob and prob.get("patterns"):
        for pattern in prob["patterns"]:
            update_schedule(pattern, attempt_data, DB_PATH)
            
    return {"status": "success", "problem_id": req.problem_id}

@app.get("/api/attempts")
def api_get_attempts(problem_id: Optional[str] = None):
    return get_attempts(DB_PATH, problem_id)

# --- Dashboard & Revision ---

@app.get("/api/revision/due")
def api_revision_due():
    return get_due_reviews(DB_PATH)

@app.get("/api/revision/stats")
def api_revision_stats():
    return get_revision_stats(DB_PATH)

@app.get("/api/stats")
def api_get_stats():
    lectures = get_all_lectures(DB_PATH)
    problems = get_all_problems(DB_PATH)
    attempts = get_attempts(DB_PATH)
    solved = get_solved_problem_ids(DB_PATH)
    
    total_lectures = len(lectures)
    processed_count = len([l for l in lectures if l.get("status") in ("identified", "matched", "completed")])
    total_problems = len(problems)
    solved_count = len(solved)
    total_attempts = len(attempts)
    
    success_attempts = [a for a in attempts if a.get("solved") == 1]
    accuracy = (len(success_attempts) / total_attempts * 100) if total_attempts > 0 else 0
    
    return {
        "total_lectures": total_lectures,
        "processed_count": processed_count,
        "total_problems": total_problems,
        "solved_count": solved_count,
        "total_attempts": total_attempts,
        "accuracy": accuracy
    }

@app.get("/api/hardware")
def api_get_hardware():
    return get_hardware_status()

# --- Logs ---

@app.get("/api/logs")
def api_get_logs(lines: int = Query(40, ge=1, le=1000)):
    if not LOG_FILE_PATH.exists():
        return {"lines": [], "path": str(LOG_FILE_PATH)}
    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            return {"lines": all_lines[-lines:], "path": str(LOG_FILE_PATH)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Settings ---

class SettingsLectureDirRequest(BaseModel):
    lecture_dir: str

@app.get("/api/settings/lecture-dir")
def api_get_lecture_dir():
    cur = config.LECTURE_DIR
    return {
        "lecture_dir": str(cur),
        "exists": cur.exists() if cur else False,
        "video_count": len(scan_videos(cur)) if cur and cur.exists() else 0
    }

@app.post("/api/settings/lecture-dir")
def api_set_lecture_dir(req: SettingsLectureDirRequest):
    raw_path = req.lecture_dir.strip().strip('"').strip("'")
    if not raw_path:
        raise HTTPException(status_code=400, detail="Lecture path cannot be empty")
    p = Path(raw_path).resolve()
    if not p.exists() or not p.is_dir():
        raise HTTPException(status_code=400, detail=f"Directory does not exist: {raw_path}")
    
    updated = update_lecture_dir(p)
    scanned = scan_videos(updated)
    return {
        "lecture_dir": str(updated),
        "exists": True,
        "video_count": len(scanned)
    }

# --- Misc ---

@app.get("/api/pipeline-hash")
def api_pipeline_hash():
    return {"hash": compute_pipeline_hash()}

# Mount static frontend
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

def open_browser_when_ready(host: str = "127.0.0.1", port: int = 8000, timeout: int = 30):
    """Background thread that verifies the server is listening and ready before opening browser."""
    def _worker():
        if os.environ.get("NO_BROWSER"):
            return
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.create_connection((host, port), timeout=1):
                    # Server is responding on port 8000, wait briefly to ensure static mounts are initialized
                    time.sleep(0.4)
                    print(f"\n[Launcher] Server is ready. Opening browser at http://localhost:{port} ...\n")
                    webbrowser.open(f"http://localhost:{port}")
                    return
            except (socket.error, ConnectionRefusedError, OSError):
                time.sleep(0.4)
    threading.Thread(target=_worker, daemon=True).start()

if __name__ == "__main__":
    open_browser_when_ready(port=8000)
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
