"""
DSA Mastery Tool — Background Pipeline Runner
Runs pipeline processing in background threads independent of Streamlit UI browser sessions.
"""
import time
import logging
import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from config import DB_PATH, TRANSCRIPTS_DIR, AUDIO_DIR
from db.schema import get_connection, get_lecture, upsert_lecture
from pipeline.transcribe import process_lecture
from pipeline.extract_concepts import process_extraction
from pipeline.identify_problem import process_identification

logger = logging.getLogger(__name__)

# Global thread-safe job registry
ACTIVE_JOBS: Dict[str, Dict[str, Any]] = {}
_jobs_lock = threading.Lock()


def _retry_with_backoff(fn, max_retries=3, base_delay=2, on_attempt=None):
    import time
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            if on_attempt:
                on_attempt(attempt, max_retries)
            return fn()
        except Exception as e:
            if isinstance(e, InterruptedError):
                raise
            last_err = e
            if attempt < max_retries:
                sleep_time = base_delay * (2 ** (attempt - 1))
                logger.warning(f"Error in {fn.__name__ if hasattr(fn, '__name__') else 'operation'}: {e}. Retrying in {sleep_time}s... (Attempt {attempt}/{max_retries})")
                time.sleep(sleep_time)
    raise last_err


def _cleanup_cancelled_lecture(lecture_id: str):
    try:
        # Do NOT delete transcript JSON if it was already produced!
        # Only clean up intermediate audio WAV and chunks
        import shutil
        for ext in ['.wav']:
            audio_path = AUDIO_DIR / f"{lecture_id}{ext}"
            if audio_path.exists():
                audio_path.unlink()
        chunks_dir = AUDIO_DIR / "chunks" / lecture_id
        if chunks_dir.exists():
            shutil.rmtree(chunks_dir, ignore_errors=True)

        # Reset DB record
        lecture = get_lecture(DB_PATH, lecture_id)
        if lecture:
            lecture["status"] = "new"
            lecture["transcript_path"] = ""
            lecture["topics"] = []
            lecture["techniques"] = []
            lecture["problems_discussed"] = []
            lecture["concept_ladder"] = []
            lecture["mcqs"] = []
            upsert_lecture(DB_PATH, lecture)

        # Remove from ACTIVE_JOBS
        with _jobs_lock:
            if lecture_id in ACTIVE_JOBS:
                del ACTIVE_JOBS[lecture_id]
                
    except Exception as e:
        logger.error(f"Error cleaning up cancelled lecture {lecture_id}: {e}")


def get_job_status(lecture_id: str) -> Dict[str, Any]:
    """Returns current active job status or DB status for a lecture."""
    with _jobs_lock:
        if lecture_id in ACTIVE_JOBS:
            job = dict(ACTIVE_JOBS[lecture_id])
            th_name = job.get("thread_name")
            if th_name and job.get("status") in ("processing", "starting"):
                is_alive = any(t.name == th_name and t.is_alive() for t in threading.enumerate())
                job["thread_alive"] = is_alive
                if not is_alive and not job.get("error"):
                    job["status"] = "error"
                    job["step_name"] = "Worker Stopped"
                    job["error"] = "Background worker thread exited."
                    ACTIVE_JOBS[lecture_id]["status"] = "error"
                    ACTIVE_JOBS[lecture_id]["thread_alive"] = False
                    ACTIVE_JOBS[lecture_id]["error"] = job["error"]
            return job
            
    # Fallback to DB status
    lecture = get_lecture(DB_PATH, lecture_id)
    if lecture:
        return {
            "lecture_id": lecture_id,
            "status": lecture.get("status", "new"),
            "step_name": "Completed" if lecture.get("status") == "completed" else "Idle",
            "progress": 100 if lecture.get("status") == "completed" else 0,
            "logs": [],
            "error": None,
            "mode": "idle",
            "attempt": 1,
            "max_attempts": 3,
            "token_count": 0,
            "tokens_per_sec": 0.0,
            "subprocess_name": "Completed",
            "model": ""
        }
        
    return {
        "lecture_id": lecture_id,
        "status": "not_found",
        "step_name": "Not Found",
        "progress": 0,
        "logs": [],
        "error": None,
        "mode": "idle",
        "attempt": 1,
        "max_attempts": 3,
        "token_count": 0,
        "tokens_per_sec": 0.0,
        "subprocess_name": "",
        "model": ""
    }


def _update_job(lecture_id: str, **kwargs):
    """Thread-safe update of active job status."""
    with _jobs_lock:
        if lecture_id not in ACTIVE_JOBS:
            ACTIVE_JOBS[lecture_id] = {
                "lecture_id": lecture_id,
                "status": "starting",
                "step_name": "Initializing",
                "progress": 0,
                "logs": [],
                "error": None,
                "started_at": datetime.now().isoformat(),
                "mode": "idle",
                "attempt": 1,
                "max_attempts": 3,
                "token_count": 0,
                "tokens_per_sec": 0.0,
                "subprocess_name": "",
                "model": ""
            }
        ACTIVE_JOBS[lecture_id].update(kwargs)
        if "log_msg" in kwargs:
            msg = f"[{datetime.now().strftime('%H:%M:%S')}] {kwargs['log_msg']}"
            ACTIVE_JOBS[lecture_id]["logs"].append(msg)
            # Keep last 100 logs
            ACTIVE_JOBS[lecture_id]["logs"] = ACTIVE_JOBS[lecture_id]["logs"][-100:]

        # Memory leak prevention: prune oldest terminal jobs if registry exceeds threshold
        if len(ACTIVE_JOBS) > 25:
            terminal_keys = [
                k for k, v in ACTIVE_JOBS.items()
                if v.get("status") in ("completed", "error", "cancelled") and not v.get("thread_alive")
            ]
            if len(terminal_keys) > 10:
                for old_key in terminal_keys[:len(terminal_keys) - 10]:
                    del ACTIVE_JOBS[old_key]


def cancel_job(lecture_id: str) -> bool:
    """Requests cancellation of an active background job."""
    with _jobs_lock:
        if lecture_id in ACTIVE_JOBS:
            status = ACTIVE_JOBS[lecture_id].get("status")
            if status in ("processing", "starting"):
                ACTIVE_JOBS[lecture_id]["cancel_requested"] = True
                ACTIVE_JOBS[lecture_id]["status"] = "cancelling"
                msg = f"[{datetime.now().strftime('%H:%M:%S')}] 🛑 Stop request received. Cancelling pipeline..."
                ACTIVE_JOBS[lecture_id]["logs"].append(msg)
                return True
    return False


def _check_cancelled(lecture_id: str):
    """Raises InterruptedError if job cancellation was requested."""
    with _jobs_lock:
        job = ACTIVE_JOBS.get(lecture_id)
        if job and job.get("cancel_requested"):
            raise InterruptedError("Pipeline processing cancelled by user.")


def run_full_pipeline_sync(
    lecture_id: str,
    skip_transcription: bool = False,
    course_context: str = ""
) -> Dict[str, Any]:
    """
    Executes all 3 pipeline steps synchronously.
    Can be called directly from CLI or from background thread.
    """
    try:
        lecture = get_lecture(DB_PATH, lecture_id)
        if not lecture:
            import os
            from config import LECTURE_DIR, VIDEO_EXTENSIONS
            from pipeline.transcribe import lecture_id_from_filename
            cand = None
            if LECTURE_DIR and Path(LECTURE_DIR).exists():
                for root, _, files in os.walk(LECTURE_DIR):
                    for file in files:
                        p = Path(root) / file
                        if p.suffix.lower() in VIDEO_EXTENSIONS:
                            if lecture_id_from_filename(p.name) == lecture_id:
                                cand = p
                                break
                    if cand:
                        break
            if cand:
                lecture = {
                    "id": lecture_id,
                    "title": cand.stem.replace('-', ' ').title(),
                    "filename": cand.name,
                    "video_path": str(cand),
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
                }
                upsert_lecture(DB_PATH, lecture)
            else:
                raise ValueError(f"Lecture '{lecture_id}' not found in database or video directory.")

        title = lecture.get("title", lecture_id)
        video_path = lecture.get("video_path", "")
        _update_job(
            lecture_id,
            status="processing",
            step_name="Step 1/3: Audio Transcription",
            progress=5,
            cancel_requested=False,
            mode="transcribing",
            attempt=1,
            max_attempts=3,
            subprocess_name="Initializing audio pipeline",
            log_msg=f"[STEP] Starting processing pipeline for '{title}'..."
        )

        _check_cancelled(lecture_id)

        # ─── Step 1: Transcription ───────────────────────────────────────────
        if not skip_transcription:
            if not video_path or not Path(video_path).exists():
                raise FileNotFoundError(f"Video file not found at path: {video_path}")

            _update_job(
                lecture_id,
                step_name="Step 1/3: Transcribing Audio via Whisper",
                progress=10,
                mode="transcribing",
                subprocess_name="FFmpeg 16kHz audio extraction",
                log_msg=f"[WHISPER] Extracting 16kHz mono audio from {Path(video_path).name}..."
            )

            def transcribe_progress_cb(current, total, detail):
                _check_cancelled(lecture_id)
                pct = int(10 + (current / max(total, 1)) * 35)
                sub_name = f"Whisper transcribing chunk {current}/{total}"
                if detail:
                    sub_name += f" ({detail})"
                _update_job(
                    lecture_id,
                    progress=pct,
                    mode="transcribing",
                    subprocess_name=sub_name,
                    log_msg=f"[WHISPER] Audio chunk {current}/{total} transcribed"
                )

            def on_step1_attempt(att, max_att):
                if att > 1:
                    _update_job(lecture_id, attempt=att, max_attempts=max_att, mode="retrying", log_msg=f"[WARN] Retrying Step 1 audio transcription (Attempt {att}/{max_att})...")

            process_lecture_with_retry = lambda: process_lecture(
                video_path,
                lecture_id,
                title,
                progress_callback=transcribe_progress_cb
            )
            _retry_with_backoff(process_lecture_with_retry, max_retries=3, base_delay=2, on_attempt=on_step1_attempt)
            _update_job(lecture_id, progress=45, mode="idle", subprocess_name="Transcription saved", log_msg="[SUCCESS] Step 1/3 Complete: Transcription saved!")
        else:
            _update_job(lecture_id, progress=45, mode="idle", subprocess_name="Using existing transcript", log_msg="[STEP] Step 1/3 Skipped: Using existing transcript file.")

        _check_cancelled(lecture_id)

        # ─── Step 2: Concept Extraction ─────────────────────────────────────
        _update_job(
            lecture_id,
            step_name="Step 2/3: LLM Concept & Code Extraction",
            progress=50,
            mode="streaming",
            attempt=1,
            max_attempts=3,
            token_count=0,
            tokens_per_sec=0.0,
            subprocess_name="Connecting to LLM & awaiting TTFT...",
            log_msg="[STEP] Step 2/3: Extracting core concepts & verbal code reconstruction via LLM..."
        )

        step2_token_info = {"count": 0, "start_time": time.time()}

        def step2_status_cb(telemetry: dict):
            _check_cancelled(lecture_id)
            _update_job(lecture_id, **telemetry)

        def step2_stream_cb(token: str):
            _check_cancelled(lecture_id)
            step2_token_info["count"] += 1
            if step2_token_info["count"] % 120 == 0:
                elapsed = time.time() - step2_token_info["start_time"]
                tok_s = round(step2_token_info["count"] / elapsed, 1) if elapsed > 0 else 0.0
                _update_job(
                    lecture_id,
                    log_msg=f"[STREAM] {step2_token_info['count']} tokens streamed ({tok_s} tok/s) · Core concepts & verbal code reconstruction"
                )

        def on_step2_attempt(att, max_att):
            if att > 1:
                _update_job(lecture_id, attempt=att, max_attempts=max_att, mode="retrying", log_msg=f"[WARN] Retrying Step 2 LLM extraction (Attempt {att}/{max_att})...")

        extraction_with_retry = lambda: process_extraction(
            lecture_id,
            course_context=course_context,
            stream_callback=step2_stream_cb,
            status_callback=step2_status_cb
        )
        extraction = _retry_with_backoff(extraction_with_retry, max_retries=3, base_delay=2, on_attempt=on_step2_attempt)

        topics_count = len(extraction.get("topics", []))
        problems_count = len(extraction.get("problems_discussed", []))
        _update_job(
            lecture_id,
            progress=75,
            mode="idle",
            subprocess_name=f"Extracted {topics_count} topics & {problems_count} problems",
            log_msg=f"[SUCCESS] Step 2/3 Complete: Extracted {topics_count} topics & {problems_count} problems!"
        )

        _check_cancelled(lecture_id)

        # ─── Step 3: Identification & Matching + MCQs ────────────────────────
        _update_job(
            lecture_id,
            step_name="Step 3/3: Unified Matching, Concept Ladder & MCQs",
            progress=80,
            mode="streaming",
            attempt=1,
            max_attempts=3,
            token_count=0,
            tokens_per_sec=0.0,
            subprocess_name="Vector indexing & candidate search (628 problems)...",
            log_msg="[STEP] Step 3/3: Running unified reasoning analysis for problem matching & MCQs..."
        )

        step3_token_info = {"count": 0, "start_time": time.time()}

        def step3_status_cb(telemetry: dict):
            _check_cancelled(lecture_id)
            _update_job(lecture_id, **telemetry)

        def step3_stream_cb(token: str):
            _check_cancelled(lecture_id)
            step3_token_info["count"] += 1
            if step3_token_info["count"] % 120 == 0:
                elapsed = time.time() - step3_token_info["start_time"]
                tok_s = round(step3_token_info["count"] / elapsed, 1) if elapsed > 0 else 0.0
                _update_job(
                    lecture_id,
                    log_msg=f"[STREAM] {step3_token_info['count']} tokens streamed ({tok_s} tok/s) · Problem matching & MCQ generation"
                )

        def on_step3_attempt(att, max_att):
            if att > 1:
                _update_job(lecture_id, attempt=att, max_attempts=max_att, mode="retrying", log_msg=f"[WARN] Retrying Step 3 reasoning (Attempt {att}/{max_att})...")

        identification_with_retry = lambda: process_identification(
            lecture_id,
            course_context=course_context,
            stream_callback=step3_stream_cb,
            status_callback=step3_status_cb
        )
        _retry_with_backoff(identification_with_retry, max_retries=3, base_delay=2, on_attempt=on_step3_attempt)

        _check_cancelled(lecture_id)

        # Mark lecture as identified in DB
        lecture = get_lecture(DB_PATH, lecture_id)
        if lecture:
            lecture["status"] = "identified"
            lecture["processed_at"] = datetime.now().isoformat()
            upsert_lecture(DB_PATH, lecture)

        _update_job(
            lecture_id,
            status="completed",
            step_name="Pipeline Completed",
            progress=100,
            mode="idle",
            subprocess_name="Completed",
            log_msg="[SUCCESS] 🎉 Pipeline completed successfully! Practice sheet & MCQs ready."
        )

        return get_job_status(lecture_id)

    except InterruptedError as ie:
        logger.info(f"Pipeline cancelled for {lecture_id}: {ie}")
        _update_job(
            lecture_id,
            status="cancelled",
            step_name="Cancelled",
            error="Processing stopped by user",
            log_msg="🛑 Pipeline processing was stopped by user."
        )
        status_copy = get_job_status(lecture_id)
        _cleanup_cancelled_lecture(lecture_id)
        return status_copy

    except Exception as e:
        err_msg = str(e)
        stack_trace = traceback.format_exc()
        logger.error(f"Pipeline error for {lecture_id}: {err_msg}\n{stack_trace}")

        # Update DB status
        # Reset DB status to 'new' on error so the user can easily retry
        # without getting stuck in a permanent 'error' state
        lecture = get_lecture(DB_PATH, lecture_id)
        if lecture:
            lecture["status"] = "new"
            upsert_lecture(DB_PATH, lecture)

        _update_job(
            lecture_id,
            status="error",
            step_name="Pipeline Failed",
            error=err_msg,
            log_msg=f"❌ Error: {err_msg}"
        )
        raise e


def start_background_job(
    lecture_id: str,
    skip_transcription: bool = False,
    course_context: str = "",
    force_restart: bool = False
) -> Optional[threading.Thread]:
    """
    Launches run_full_pipeline in a detached daemon background thread.
    Thread-safe and strictly guarantees only ONE active worker thread per lecture_id.
    """
    with _jobs_lock:
        # 1. Check if a worker thread for this lecture is already running in Python
        for th in threading.enumerate():
            if th.name == f"PipelineWorker-{lecture_id}" and th.is_alive():
                logger.warning(f"Worker thread for '{lecture_id}' is already alive and running. Ignoring duplicate start request.")
                return None

        job = ACTIVE_JOBS.get(lecture_id, {})
        status = job.get("status")

        if not force_restart:
            if status in ("processing", "starting", "cancelling"):
                logger.warning(f"Job for '{lecture_id}' is already active (status={status}). Rejecting start.")
                return None
            if status in ("completed", "identified", "matched", "transcribed", "extracted"):
                logger.info(f"Job for '{lecture_id}' is already in state '{status}'. Skipping start.")
                return None

        def worker():
            try:
                run_full_pipeline_sync(
                    lecture_id,
                    skip_transcription=skip_transcription,
                    course_context=course_context
                )
            except Exception as e:
                err_msg = str(e)
                logger.error(f"Background thread error for {lecture_id}: {err_msg}")
                _update_job(
                    lecture_id,
                    status="error",
                    step_name="Pipeline Failed",
                    error=err_msg,
                    thread_alive=False,
                    log_msg=f"❌ Error: {err_msg}"
                )
            finally:
                with _jobs_lock:
                    if lecture_id in ACTIVE_JOBS:
                        ACTIVE_JOBS[lecture_id]["thread_alive"] = False

        thread = threading.Thread(
            target=worker,
            name=f"PipelineWorker-{lecture_id}",
            daemon=False
        )

        ACTIVE_JOBS[lecture_id] = {
            "lecture_id": lecture_id,
            "status": "processing",
            "step_name": "Starting Background Thread",
            "progress": 1,
            "thread_name": thread.name,
            "thread_alive": True,
            "cancel_requested": False,
            "logs": [f"[{datetime.now().strftime('%H:%M:%S')}] Detached background worker thread started for {lecture_id}."],
            "error": None,
            "started_at": datetime.now().isoformat()
        }

        thread.start()
        return thread
