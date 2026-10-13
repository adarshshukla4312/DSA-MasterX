import os
import re
import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional
import ffmpeg

from config import (
    LECTURE_DIR,
    AUDIO_DIR,
    TRANSCRIPTS_DIR,
    VIDEO_EXTENSIONS,
    WHISPER_MODEL,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
    WHISPER_HETEROGENEOUS_MODE,
    WHISPER_CPU_THREADS_HETERO,
    WHISPER_CPU_THREADS_SOLO,
    OPENVINO_WHISPER_MODEL,
    DB_PATH
)
from db.schema import get_lecture, upsert_lecture
from pipeline.power import get_power_status
from pipeline.transcribe_openvino import is_intel_igpu_available
from pipeline.heterogeneous import HeterogeneousTranscriber

logger = logging.getLogger(__name__)

# Lazy loaded whisper model
_whisper_model = None

DSA_INITIAL_PROMPT = (
    "DSA, Data Structures, Algorithms, LeetCode, GeeksForGeeks, Arrays, LinkedList, "
    "Binary Tree, HashMap, Stack, Queue, Recursion, Dynamic Programming, Kadane, "
    "BFS, DFS, amortized, inorder, preorder, postorder, Big-O, time complexity, "
    "prefix sum, two pointers, sliding window, backtracking, greedy"
)


def get_whisper_model(model_size, device, compute_type, force_cpu: bool = False):
    global _whisper_model
    if force_cpu or _whisper_model is None:
        from faster_whisper import WhisperModel
        
        # Maximize multi-core throughput across all cores and threads
        avail_cpus = os.cpu_count() or 12
        os.environ["OMP_NUM_THREADS"] = str(avail_cpus)
        os.environ["MKL_NUM_THREADS"] = str(avail_cpus)
        
        target_device = "cpu" if force_cpu else device
        target_compute = "int8" if force_cpu else compute_type
        
        logger.info(f"Loading Whisper model '{model_size}' on {target_device} ({target_compute}) using all {avail_cpus} CPU threads...")
        try:
            _whisper_model = WhisperModel(
                model_size,
                device=target_device,
                compute_type=target_compute,
                cpu_threads=avail_cpus,
                num_workers=1
            )
        except Exception as e:
            logger.warning(f"Failed to load Whisper on {target_device}/{target_compute} ({e}). Falling back to CPU int8...")
            _whisper_model = WhisperModel(
                model_size,
                device="cpu",
                compute_type="int8",
                cpu_threads=avail_cpus,
                num_workers=1
            )
            
    return _whisper_model


def lecture_id_from_filename(filename: str) -> str:
    """Generates a clean ID from a filename (e.g., '22-arrays-prefix-sum')."""
    base = Path(filename).stem
    clean_id = re.sub(r'[^a-zA-Z0-9]+', '-', base).strip('-').lower()
    return clean_id


def scan_lectures(lecture_dir: Path | str) -> list[dict]:
    """Scans LECTURE_DIR for video files, returns list of info dicts."""
    lecture_dir = Path(lecture_dir)
    lectures = []
    
    if not lecture_dir.exists():
        return lectures

    ignore_dirs = {
        "transcript", "transcripts", "dsa-tool", "data", "audio", "db", "frontend",
        "pages", "pipeline", "prompts", "revision", "scratch", "scripts", "__pycache__",
        ".git", ".venv", "venv", "env", "node_modules", ".gemini", ".idea", ".vscode"
    }

    for root, dirs, files in os.walk(lecture_dir):
        dirs[:] = [d for d in dirs if d.lower() not in ignore_dirs and not d.startswith(".")]
        for file in files:
            file_path = Path(root) / file
            if file_path.is_file() and file_path.suffix.lower() in VIDEO_EXTENSIONS:
                filename = file_path.name
                lecture_id = lecture_id_from_filename(filename)
                title = file_path.stem.replace('-', ' ').title()
                
                lectures.append({
                    "filename": filename,
                    "title": title,
                    "video_path": str(file_path),
                    "lecture_id": lecture_id,
                    "status": "new"
                })
            
    return lectures


def extract_audio(video_path: str, output_dir: Path | str) -> Path:
    """Uses ffmpeg-python to extract 16kHz mono WAV."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    video_path_obj = Path(video_path)
    audio_filename = f"{lecture_id_from_filename(video_path_obj.name)}.wav"
    audio_path = output_dir / audio_filename
    
    if audio_path.exists():
        logger.info(f"Audio already exists: {audio_path}")
        return audio_path
        
    logger.info(f"Extracting audio from {video_path} to {audio_path}")
    
    ffmpeg_binary = shutil.which("ffmpeg") or "ffmpeg"
    
    import time
    for attempt in range(1, 4):
        try:
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(stream, str(audio_path), acodec='pcm_s16le', ac=1, ar='16k')
            stream = ffmpeg.overwrite_output(stream)
            ffmpeg.run(stream, cmd=ffmpeg_binary, quiet=True)
            break
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error (attempt {attempt}): {e.stderr.decode() if e.stderr else str(e)}")
            if attempt == 3: raise
            time.sleep(2 * attempt)
        except Exception as e:
            logger.error(f"Failed to execute FFmpeg (attempt {attempt}): {e}")
            if attempt == 3: raise
            time.sleep(2 * attempt)
        
    return audio_path


def chunk_audio_if_needed(audio_path: Path, chunk_seconds: int = 600) -> list[tuple[Path, float]]:
    """
    Slices audio into chunks of `chunk_seconds` (default 10 mins) using FFmpeg.
    Returns list of (chunk_file_path, start_offset_seconds).
    """
    ffmpeg_binary = shutil.which("ffmpeg") or "ffmpeg"
    chunks_dir = audio_path.parent / "chunks" / audio_path.stem
    chunks_dir.mkdir(parents=True, exist_ok=True)
    
    existing_chunks = sorted(list(chunks_dir.glob("chunk_*.wav")))
    if existing_chunks:
        results = []
        for idx, chunk_f in enumerate(existing_chunks):
            results.append((chunk_f, float(idx * chunk_seconds)))
        return results

    logger.info(f"Segmenting {audio_path.name} into {chunk_seconds//60}-minute chunks for ultra-low memory usage...")
    pattern = str(chunks_dir / "chunk_%03d.wav")
    
    cmd = [
        ffmpeg_binary, "-y", "-i", str(audio_path),
        "-f", "segment", "-segment_time", str(chunk_seconds),
        "-c", "copy", pattern
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        logger.warning(f"FFmpeg chunking error ({e}), proceeding with full file...")
        return [(audio_path, 0.0)]

    created_chunks = sorted(list(chunks_dir.glob("chunk_*.wav")))
    results = []
    for idx, chunk_f in enumerate(created_chunks):
        results.append((chunk_f, float(idx * chunk_seconds)))
    return results if results else [(audio_path, 0.0)]


def transcribe_audio(
    audio_path: str | Path,
    model_size: str,
    device: str,
    compute_type: str,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> dict:
    """
    Transcribes audio with automatic power-aware heterogeneous acceleration:
    - If plugged in & Intel iGPU is available: runs parallel CPU (6 threads) + iGPU (OpenVINO INT8)
    - If on battery or CPU mode: runs single-engine 12-thread INT8 CPU transcription
    """
    audio_path = Path(audio_path)
    chunks = chunk_audio_if_needed(audio_path, chunk_seconds=600)
    total_chunks = len(chunks)
    logger.info(f"Preparing to transcribe {audio_path.name} across {total_chunks} chunk(s)...")

    # Assess power topology and hardware availability
    power = get_power_status()
    igpu_avail, igpu_name = is_intel_igpu_available()

    use_heterogeneous = (
        WHISPER_HETEROGENEOUS_MODE in ("auto", "heterogeneous")
        and (power.is_plugged_in or WHISPER_HETEROGENEOUS_MODE == "heterogeneous")
        and igpu_avail
        and total_chunks > 1
    )

    if use_heterogeneous:
        logger.info(
            f"⚡ Activating Heterogeneous Parallel Transcription: System plugged in ({power.status_text}). "
            f"Dispatching {total_chunks} chunks to CPU ({WHISPER_CPU_THREADS_HETERO} threads) + {igpu_name}..."
        )
        if progress_callback:
            progress_callback(
                0,
                total_chunks,
                f"⚡ Starting dual CPU+iGPU parallel transcription ({total_chunks} chunks, {power.status_text})..."
            )

        transcriber = HeterogeneousTranscriber(
            chunks=chunks,
            initial_prompt=DSA_INITIAL_PROMPT,
            progress_callback=progress_callback,
            cpu_threads=WHISPER_CPU_THREADS_HETERO,
            openvino_model_id=OPENVINO_WHISPER_MODEL
        )
        return transcriber.run()

    # Fallback / Battery Mode: CPU-only execution with full thread budget
    if not power.is_plugged_in:
        logger.info(f"🔋 System on Battery ({power.battery_percent}%). Running CPU-only mode with {WHISPER_CPU_THREADS_SOLO} threads to conserve power.")
    else:
        logger.info(f"💻 Running standard CPU transcription with {WHISPER_CPU_THREADS_SOLO} threads.")

    model = get_whisper_model(model_size, device, compute_type)
    
    segment_list = []
    full_text_parts = []
    total_duration = 0.0
    detected_language = "en"
    
    vad_params = dict(
        threshold=0.35,
        min_speech_duration_ms=500,
        speech_pad_ms=200,
        min_silence_duration_ms=500
    )
    
    for idx, (chunk_file, time_offset) in enumerate(chunks, 1):
        detail_msg = f"Transcribing audio chunk {idx} of {total_chunks} ({time_offset//60:.0f}m - {(time_offset+600)//60:.0f}m in lecture)..."
        logger.info(detail_msg)
        if progress_callback:
            progress_callback(idx, total_chunks, detail_msg)

        import time
        for attempt in range(1, 3):
            try:
                try:
                    # CPU Optimization: beam_size=1 (greedy search) is 3-4x faster on CPU
                    segments, info = model.transcribe(
                        str(chunk_file),
                        language="en",
                        beam_size=1,
                        best_of=1,
                        temperature=0.0,
                        condition_on_previous_text=False,
                        initial_prompt=DSA_INITIAL_PROMPT,
                        vad_filter=True,
                        vad_parameters=vad_params
                    )
                    chunk_segments = list(segments)
                except RuntimeError as e:
                    if "cublas" in str(e).lower() or "cuda" in str(e).lower():
                        logger.warning(f"CUDA error ({e}). Switching to CPU int8 mode...")
                        model = get_whisper_model(model_size, "cpu", "int8", force_cpu=True)
                        segments, info = model.transcribe(
                            str(chunk_file),
                            language="en",
                            beam_size=1,
                            best_of=1,
                            temperature=0.0,
                            condition_on_previous_text=False,
                            initial_prompt=DSA_INITIAL_PROMPT,
                            vad_filter=True,
                            vad_parameters=vad_params
                        )
                        chunk_segments = list(segments)
                    else:
                        raise
                break
            except Exception as e:
                logger.warning(f"Error transcribing chunk (attempt {attempt}/2): {e}")
                if attempt == 2: raise
                time.sleep(2)

        detected_language = getattr(info, "language", "en")
        total_duration += getattr(info, "duration", 0.0)
        
        for s in chunk_segments:
            adjusted_start = round(s.start + time_offset, 2)
            adjusted_end = round(s.end + time_offset, 2)
            text = s.text.strip()
            if text:
                segment_list.append({
                    "start": adjusted_start,
                    "end": adjusted_end,
                    "text": text
                })
                full_text_parts.append(text)

    return {
        "segments": segment_list,
        "full_text": " ".join(full_text_parts),
        "language": detected_language,
        "duration": round(total_duration, 2),
        "engine": "cpu"
    }


def save_transcript(lecture_id: str, title: str, transcript_data: dict, output_dir: Path | str) -> Path:
    """Saves JSON transcript to output_dir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    out_file = output_dir / f"{lecture_id}.json"
    data = {
        "lecture_id": lecture_id,
        "title": title,
        "language": transcript_data.get("language"),
        "duration": transcript_data.get("duration"),
        "full_text": transcript_data.get("full_text"),
        "segments": transcript_data.get("segments", []),
        "engine": transcript_data.get("engine", "cpu"),
        "worker_stats": transcript_data.get("worker_stats"),
        "elapsed_seconds": transcript_data.get("elapsed_seconds")
    }
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    return out_file


def cleanup_audio(audio_path: str | Path) -> None:
    """Deletes intermediate .wav file and its chunk directory to save disk space."""
    audio_path = Path(audio_path)
    try:
        # Delete chunk directory if present
        chunks_dir = audio_path.parent / "chunks" / audio_path.stem
        if chunks_dir.exists():
            shutil.rmtree(chunks_dir, ignore_errors=True)
            logger.info(f"Cleaned up audio chunks: {chunks_dir}")

        # Delete main audio .wav file
        if audio_path.exists():
            audio_path.unlink()
            logger.info(f"Cleaned up audio file: {audio_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup audio for {audio_path}: {e}")


def process_lecture(
    video_path: str,
    lecture_id: str,
    title: str,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Path:
    """Full pipeline: extract audio → transcribe → save → update DB status → cleanup audio"""
    logger.info(f"Processing lecture: {title} ({lecture_id})")
    
    audio_path = extract_audio(video_path, AUDIO_DIR)
    transcript_data = transcribe_audio(
        audio_path,
        WHISPER_MODEL,
        WHISPER_DEVICE,
        WHISPER_COMPUTE_TYPE,
        progress_callback=progress_callback
    )
    transcript_path = save_transcript(lecture_id, title, transcript_data, TRANSCRIPTS_DIR)
    
    lecture = get_lecture(DB_PATH, lecture_id) or {
        "id": lecture_id,
        "title": title,
        "filename": Path(video_path).name,
        "video_path": video_path
    }
    
    lecture["transcript_path"] = str(transcript_path)
    lecture["status"] = "transcribed"
    upsert_lecture(DB_PATH, lecture)
    
    # Automatically clean up intermediate WAV files to free disk space
    cleanup_audio(audio_path)
    
    logger.info(f"Finished transcribing {lecture_id}")
    return transcript_path

