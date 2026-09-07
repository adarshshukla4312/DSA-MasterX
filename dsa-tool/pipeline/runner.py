"""
DSA Mastery Tool — Background Pipeline Runner
Runs pipeline processing in background threads independent of Streamlit UI browser sessions.
"""
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


def _retry_with_backoff(fn, max_retries=3, base_delay=2):
    import time
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
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
        # Delete transcript JSON
        transcript_path = TRANSCRIPTS_DIR / f"{lecture_id}.json"
        if transcript_path.exists():
            transcript_path.unlink()
            
        # Delete audio WAV and chunks
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
            return dict(ACTIVE_JOBS[lecture_id])
            
    # Fallback to DB status
    lecture = get_lecture(DB_PATH, lecture_id)
    if lecture:
        return {
            "lecture_id": lecture_id,
            "status": lecture.get("status", "new"),
            "step_name": "Completed" if lecture.get("status") == "completed" else "Idle",
            "progress": 100 if lecture.get("status") == "completed" else 0,
            "logs": [],
            "error": None
        }
        
    return {
        "lecture_id": lecture_id,
        "status": "not_found",
        "step_name": "Not Found",
        "progress": 0,
        "logs": [],
        "error": None
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
                "started_at": datetime.now().isoformat()
            }
        ACTIVE_JOBS[lecture_id].update(kwargs)
        if "log_msg" in kwargs:
            msg = f"[{datetime.now().strftime('%H:%M:%S')}] {kwargs['log_msg']}"
            ACTIVE_JOBS[lecture_id]["logs"].append(msg)
            # Keep last 50 logs
            ACTIVE_JOBS[lecture_id]["logs"] = ACTIVE_JOBS[lecture_id]["logs"][-50:]


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
    lecture = get_lecture(DB_PATH, lecture_id)
    if not lecture:
        raise ValueError(f"Lecture '{lecture_id}' not found in database.")

    title = lecture.get("title", lecture_id)
    video_path = lecture.get("video_path", "")

    try:
        _update_job(
            lecture_id,
            status="processing",
            step_name="Step 1/3: Audio Transcription",
            progress=5,
            cancel_requested=False,
            log_msg=f"Starting processing pipeline for '{title}'..."
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
                log_msg=f"Extracting & transcribing audio from {Path(video_path).name}..."
            )

            def transcribe_progress_cb(current, total, detail):
                _check_cancelled(lecture_id)
                pct = int(10 + (current / max(total, 1)) * 35)
                _update_job(
                    lecture_id,
                    progress=pct,
                    log_msg=f"Transcribing chunk {current}/{total}..."
                )

            process_lecture_with_retry = lambda: process_lecture(
                video_path,
                lecture_id,
                title,
                progress_callback=transcribe_progress_cb
            )
            _retry_with_backoff(process_lecture_with_retry, max_retries=3, base_delay=2)
            _update_job(lecture_id, progress=45, log_msg="Step 1/3 Complete: Transcription saved!")
        else:
            _update_job(lecture_id, progress=45, log_msg="Step 1/3 Skipped: Using existing transcript file.")

        _check_cancelled(lecture_id)

        # ─── Step 2: Concept Extraction ─────────────────────────────────────
        _update_job(
            lecture_id,
            step_name="Step 2/3: LLM Concept & Code Extraction",
            progress=50,
            log_msg="Extracting core concepts & verbal code reconstruction via LLM..."
        )

        def extraction_stream_cb(token):
            # Keep log of live tokens
            pass

        extraction_with_retry = lambda: process_extraction(
            lecture_id,
            course_context=course_context,
            stream_callback=extraction_stream_cb
        )
        extraction = _retry_with_backoff(extraction_with_retry, max_retries=3, base_delay=2)

        topics_count = len(extraction.get("topics", []))
        problems_count = len(extraction.get("problems_discussed", []))
        _update_job(
            lecture_id,
            progress=75,
            log_msg=f"Step 2/3 Complete: Extracted {topics_count} topics & {problems_count} problems!"
        )

        _check_cancelled(lecture_id)

        # ─── Step 3: Identification & Matching + MCQs ────────────────────────
        _update_job(
            lecture_id,
            step_name="Step 3/3: Unified Matching, Concept Ladder & MCQs",
            progress=80,
            log_msg="Running unified reasoning analysis for problem matching & MCQs..."
        )

        identification_with_retry = lambda: process_identification(
            lecture_id,
            course_context=course_context
        )
        _retry_with_backoff(identification_with_retry, max_retries=3, base_delay=2)

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
            log_msg="🎉 Pipeline completed successfully! Practice sheet & MCQs ready."
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
                logger.error(f"Background thread error for {lecture_id}: {e}")

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
