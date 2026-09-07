"""
Pipeline Version & Hash Computation
Provides smart change detection so the UI can detect when prompts, code, or model settings change.
"""
import hashlib
from pathlib import Path
from config import BASE_DIR, LLM_STANDARD_MODEL, LLM_REASONING_MODEL, WHISPER_MODEL, LLM_THINKING


def compute_pipeline_hash() -> str:
    """Computes a SHA-256 hash of all processing pipeline prompts, configs, and core code files."""
    components = []

    # 1. Prompts
    prompts_dir = BASE_DIR / "prompts"
    if prompts_dir.exists():
        for prompt_file in sorted(prompts_dir.glob("*.txt")):
            try:
                components.append(prompt_file.read_text(encoding="utf-8"))
            except Exception:
                pass

    # 2. Config parameters
    components.append(f"LLM_STANDARD_MODEL={LLM_STANDARD_MODEL}")
    components.append(f"LLM_REASONING_MODEL={LLM_REASONING_MODEL}")
    components.append(f"WHISPER_MODEL={WHISPER_MODEL}")
    components.append(f"LLM_THINKING={LLM_THINKING}")

    # 3. Pipeline code files
    pipeline_dir = BASE_DIR / "pipeline"
    if pipeline_dir.exists():
        for py_file in ["transcribe.py", "extract_concepts.py", "identify_problem.py", "recommend.py"]:
            f = pipeline_dir / py_file
            if f.exists():
                try:
                    components.append(f.read_text(encoding="utf-8"))
                except Exception:
                    pass

    combined = "\n---\n".join(components)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]
