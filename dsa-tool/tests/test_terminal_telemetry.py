"""
Unit tests for terminal telemetry and status reporting:
Verifies mode detection, attempt counters, token counting, and job status schema.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.runner import _update_job, get_job_status, ACTIVE_JOBS, _jobs_lock

def test_job_telemetry_schema():
    lecture_id = "test-lecture-telemetry-01"
    
    _update_job(
        lecture_id,
        status="processing",
        step_name="Step 2/3: LLM Concept & Code Extraction",
        progress=55,
        mode="streaming",
        attempt=1,
        max_attempts=3,
        token_count=350,
        tokens_per_sec=28.4,
        subprocess_name="Streaming deepseek-chat tokens",
        model="deepseek/deepseek-chat",
        log_msg="[STREAM] 350 tokens streamed (28.4 tok/s) · Core concepts & verbal code reconstruction"
    )
    
    status = get_job_status(lecture_id)
    assert status["status"] == "processing"
    assert status["mode"] == "streaming"
    assert status["attempt"] == 1
    assert status["max_attempts"] == 3
    assert status["token_count"] == 350
    assert status["tokens_per_sec"] == 28.4
    assert status["subprocess_name"] == "Streaming deepseek-chat tokens"
    assert status["model"] == "deepseek/deepseek-chat"
    assert len(status["logs"]) >= 1
    assert "[STREAM]" in status["logs"][-1]
    
    # Test retry state
    _update_job(
        lecture_id,
        mode="retrying",
        attempt=2,
        log_msg="[WARN] Retrying Step 2 LLM extraction (Attempt 2/3)..."
    )
    status2 = get_job_status(lecture_id)
    assert status2["mode"] == "retrying"
    assert status2["attempt"] == 2
    assert "[WARN]" in status2["logs"][-1]

    # Clean up test job
    with _jobs_lock:
        if lecture_id in ACTIVE_JOBS:
            del ACTIVE_JOBS[lecture_id]

if __name__ == "__main__":
    test_job_telemetry_schema()
    print("PASS: test_job_telemetry_schema")
    print("\nAll terminal telemetry tests passed successfully!")
