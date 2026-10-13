"""
DSA Mastery Tool — Heterogeneous Parallel Transcriber
Executes dynamic work-stealing transcription concurrently across CPU cores (CTranslate2 INT8)
and Intel iGPU (OpenVINO GenAI INT8) with strict chronological barrier synchronization.
"""
import time
import queue
import logging
import threading
from pathlib import Path
from typing import Callable, Optional, List, Tuple, Dict, Any

from config import (
    WHISPER_MODEL,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
    WHISPER_CPU_THREADS_HETERO,
    OPENVINO_WHISPER_MODEL
)
from pipeline.transcribe_openvino import (
    is_intel_igpu_available,
    transcribe_chunk_openvino
)

logger = logging.getLogger(__name__)


class HeterogeneousTranscriber:
    """
    Manages dual-worker parallel transcription with a dynamic work queue
    and a chronological barrier.
    """
    def __init__(
        self,
        chunks: List[Tuple[Path, float]],
        initial_prompt: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        cpu_threads: int = WHISPER_CPU_THREADS_HETERO,
        openvino_model_id: str = OPENVINO_WHISPER_MODEL
    ):
        self.chunks = chunks
        self.total_chunks = len(chunks)
        self.initial_prompt = initial_prompt
        self.progress_callback = progress_callback
        self.cpu_threads = cpu_threads
        self.openvino_model_id = openvino_model_id

        self.work_queue: queue.Queue[Tuple[int, Path, float]] = queue.Queue()
        self.results: Dict[int, Tuple[List[Dict[str, Any]], float]] = {}
        self.results_lock = threading.Lock()
        self.completed_count = 0
        self.stop_event = threading.Event()
        self.errors: List[Exception] = []
        self.worker_stats = {"cpu": 0, "igpu": 0}

        # Populate dynamic work queue with all chunks
        for idx, (chunk_file, time_offset) in enumerate(self.chunks):
            self.work_queue.put((idx, chunk_file, time_offset))

    def _cpu_worker(self):
        """Worker 1: CTranslate2 INT8 on CPU with allocated thread budget."""
        from faster_whisper import WhisperModel

        logger.info(f"[CPU Worker] Initializing Faster-Whisper with {self.cpu_threads} threads...")
        try:
            model = WhisperModel(
                WHISPER_MODEL,
                device="cpu",
                compute_type="int8",
                cpu_threads=self.cpu_threads,
                num_workers=1
            )
        except Exception as e:
            logger.error(f"[CPU Worker] Failed to initialize Whisper model: {e}")
            self.errors.append(e)
            return

        vad_params = dict(
            threshold=0.35,
            min_speech_duration_ms=500,
            speech_pad_ms=200,
            min_silence_duration_ms=500
        )

        while not self.stop_event.is_set():
            try:
                idx, chunk_file, time_offset = self.work_queue.get_nowait()
            except queue.Empty:
                break

            logger.info(f"[CPU Worker] Transcribing chunk {idx + 1}/{self.total_chunks} ({chunk_file.name})...")
            chunk_success = False
            for attempt in range(1, 3):
                try:
                    segments, info = model.transcribe(
                        str(chunk_file),
                        language="en",
                        beam_size=1,
                        best_of=1,
                        temperature=0.0,
                        condition_on_previous_text=False,
                        initial_prompt=self.initial_prompt,
                        vad_filter=True,
                        vad_parameters=vad_params
                    )
                    chunk_segments = []
                    for s in segments:
                        text = s.text.strip()
                        if text:
                            chunk_segments.append({
                                "start": round(s.start + time_offset, 2),
                                "end": round(s.end + time_offset, 2),
                                "text": text
                            })
                    dur = getattr(info, "duration", 600.0)

                    with self.results_lock:
                        self.results[idx] = (chunk_segments, dur)
                        self.completed_count += 1
                        self.worker_stats["cpu"] += 1
                        current_done = self.completed_count

                    detail = f"Chunk {idx + 1}/{self.total_chunks} transcribed [CPU worker] ({current_done}/{self.total_chunks} done)"
                    logger.info(f"[CPU Worker] {detail}")
                    if self.progress_callback:
                        self.progress_callback(current_done, self.total_chunks, detail)

                    chunk_success = True
                    break
                except Exception as e:
                    logger.warning(f"[CPU Worker] Error on chunk {idx + 1} (attempt {attempt}/2): {e}")
                    time.sleep(1)

            if not chunk_success:
                err_msg = f"[CPU Worker] Failed chunk {idx + 1} after 2 attempts."
                logger.error(err_msg)
                self.errors.append(RuntimeError(err_msg))

            self.work_queue.task_done()

        logger.info("[CPU Worker] Finished all assigned chunks.")

    def _igpu_worker(self):
        """Worker 2: OpenVINO INT8 on Intel Iris Xe iGPU."""
        logger.info(f"[iGPU Worker] Starting OpenVINO worker on Intel iGPU ({self.openvino_model_id})...")

        while not self.stop_event.is_set():
            try:
                idx, chunk_file, time_offset = self.work_queue.get_nowait()
            except queue.Empty:
                break

            logger.info(f"[iGPU Worker] Transcribing chunk {idx + 1}/{self.total_chunks} ({chunk_file.name})...")
            try:
                chunk_segments, dur = transcribe_chunk_openvino(
                    chunk_file=chunk_file,
                    time_offset=time_offset,
                    initial_prompt=self.initial_prompt,
                    model_id=self.openvino_model_id
                )

                with self.results_lock:
                    self.results[idx] = (chunk_segments, dur)
                    self.completed_count += 1
                    self.worker_stats["igpu"] += 1
                    current_done = self.completed_count

                detail = f"Chunk {idx + 1}/{self.total_chunks} transcribed [iGPU worker] ({current_done}/{self.total_chunks} done)"
                logger.info(f"[iGPU Worker] {detail}")
                if self.progress_callback:
                    self.progress_callback(current_done, self.total_chunks, detail)

                self.work_queue.task_done()
            except Exception as e:
                logger.warning(f"[iGPU Worker] Failed to process chunk {idx + 1} on iGPU ({e}). Returning chunk to queue for CPU fallback...")
                # Return chunk to work queue for the CPU worker to salvage
                self.work_queue.put((idx, chunk_file, time_offset))
                self.work_queue.task_done()
                logger.warning("[iGPU Worker] Exiting iGPU worker thread to allow safe CPU completion.")
                break

        logger.info("[iGPU Worker] Finished.")

    def run(self) -> Dict[str, Any]:
        """
        Launches both workers concurrently, waits at the barrier,
        and reconstructs chronological segments.
        """
        logger.info(f"⚡ Launching Heterogeneous Transcription ({self.total_chunks} chunks)...")
        start_time = time.time()

        t_cpu = threading.Thread(target=self._cpu_worker, name="CPU-Whisper-Worker", daemon=True)
        t_igpu = threading.Thread(target=self._igpu_worker, name="iGPU-Whisper-Worker", daemon=True)

        t_cpu.start()
        t_igpu.start()

        # Barrier: Wait for both worker threads to conclude all work
        t_cpu.join()
        t_igpu.join()

        elapsed = time.time() - start_time
        logger.info(
            f"⚡ Barrier reached in {elapsed:.1f}s! Work distribution: "
            f"CPU={self.worker_stats['cpu']} chunks, iGPU={self.worker_stats['igpu']} chunks."
        )

        if self.errors:
            raise RuntimeError(f"Transcription failed with errors: {self.errors}")

        # Chronological verification barrier
        missing = [i for i in range(self.total_chunks) if i not in self.results]
        if missing:
            raise RuntimeError(f"Transcription incomplete! Missing chunks: {missing}")

        all_segments = []
        full_text_parts = []
        total_duration = 0.0

        for idx in sorted(self.results.keys()):
            chunk_segs, dur = self.results[idx]
            total_duration += dur
            for s in chunk_segs:
                all_segments.append(s)
                if s.get("text"):
                    full_text_parts.append(s["text"])

        return {
            "segments": all_segments,
            "full_text": " ".join(full_text_parts),
            "language": "en",
            "duration": round(total_duration, 2),
            "engine": "heterogeneous (CPU+Intel iGPU)",
            "worker_stats": self.worker_stats,
            "elapsed_seconds": round(elapsed, 2)
        }
