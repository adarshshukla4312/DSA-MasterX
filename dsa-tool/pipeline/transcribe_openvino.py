"""
DSA Mastery Tool — OpenVINO Intel iGPU Transcription Worker
Accelerates Whisper inference on Intel integrated GPUs (Iris Xe / Arc) using OpenVINO GenAI.
"""
import os
import logging
import threading
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger(__name__)

_ov_pipeline = None
_ov_lock = threading.Lock()
_igpu_checked = False
_igpu_available = False
_igpu_name = ""


def is_intel_igpu_available() -> Tuple[bool, str]:
    """
    Checks if OpenVINO can access the Intel iGPU ('GPU' device).
    Returns (is_available, device_name).
    """
    global _igpu_checked, _igpu_available, _igpu_name
    if _igpu_checked:
        return _igpu_available, _igpu_name

    try:
        import openvino as ov
        import openvino_genai as ov_genai
        core = ov.Core()
        devices = core.available_devices
        if "GPU" in devices:
            try:
                name = core.get_property("GPU", "FULL_DEVICE_NAME")
            except Exception:
                name = "Intel iGPU"
            _igpu_available = True
            _igpu_name = str(name)
        else:
            _igpu_available = False
            _igpu_name = "No Intel GPU found in OpenVINO devices"
    except Exception as e:
        _igpu_available = False
        _igpu_name = f"OpenVINO not available ({e})"

    _igpu_checked = True
    return _igpu_available, _igpu_name


def get_openvino_whisper_pipeline(
    model_id: str = "OpenVINO/whisper-small-int8-ov",
    device: str = "GPU"
):
    """
    Thread-safe lazy initializer for OpenVINO GenAI WhisperPipeline on Intel iGPU.
    """
    global _ov_pipeline
    with _ov_lock:
        if _ov_pipeline is not None:
            return _ov_pipeline

        import openvino_genai as ov_genai
        from huggingface_hub import snapshot_download

        # Check local cache first to avoid network latency
        model_path = None
        try:
            model_path = snapshot_download(model_id, local_files_only=True)
            logger.info(f"Loaded OpenVINO Whisper model from local cache: {model_path}")
        except Exception:
            logger.info(f"Model not in local cache; downloading {model_id} from HuggingFace...")
            model_path = snapshot_download(model_id, local_files_only=False)

        logger.info(f"Compiling OpenVINO Whisper model on {device} ({model_id})...")
        _ov_pipeline = ov_genai.WhisperPipeline(str(model_path), device)
        logger.info(f"OpenVINO Whisper pipeline successfully compiled on {device}!")
        return _ov_pipeline


def transcribe_chunk_openvino(
    chunk_file: Path | str,
    time_offset: float = 0.0,
    initial_prompt: Optional[str] = None,
    model_id: str = "OpenVINO/whisper-small-int8-ov"
) -> Tuple[List[Dict[str, Any]], float]:
    """
    Transcribes a single audio chunk using OpenVINO GenAI on Intel iGPU.
    Returns (segment_list, chunk_duration).
    """
    from faster_whisper.audio import decode_audio

    chunk_path = Path(chunk_file)
    if not chunk_path.exists():
        raise FileNotFoundError(f"Chunk file not found: {chunk_path}")

    # Decode audio to 16kHz mono float32 array
    audio_arr = decode_audio(str(chunk_path), sampling_rate=16000)
    chunk_duration = float(len(audio_arr)) / 16000.0

    pipe = get_openvino_whisper_pipeline(model_id=model_id, device="GPU")

    gen_kwargs = {
        "language": "<|en|>",
        "task": "transcribe",
        "return_timestamps": True
    }
    if initial_prompt:
        gen_kwargs["initial_prompt"] = initial_prompt

    res = pipe.generate(audio_arr, **gen_kwargs)

    segment_list = []
    if hasattr(res, "chunks") and res.chunks:
        for c in res.chunks:
            text = c.text.strip()
            if not text:
                continue

            start_ts = float(c.start_ts) if c.start_ts >= 0 else 0.0
            end_ts = float(c.end_ts) if c.end_ts >= 0 else (start_ts + 1.0)
            if end_ts > chunk_duration:
                end_ts = chunk_duration

            adjusted_start = round(start_ts + time_offset, 2)
            adjusted_end = round(end_ts + time_offset, 2)

            segment_list.append({
                "start": adjusted_start,
                "end": adjusted_end,
                "text": text
            })
    elif hasattr(res, "texts") and res.texts:
        # Fallback if no chunk timestamps were returned
        combined_text = " ".join(t.strip() for t in res.texts if t.strip())
        if combined_text:
            segment_list.append({
                "start": round(time_offset, 2),
                "end": round(time_offset + chunk_duration, 2),
                "text": combined_text
            })

    return segment_list, chunk_duration
