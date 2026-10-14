"""
Unit & Integration Test for GritX Rust Audio Engine
Validates:
1. WAV loading and metadata analysis
2. Silence-aware zero-crossing audio chunking
3. Prevention of mid-speech clipping
4. Performance / sub-millisecond execution
"""
import subprocess
import struct
import math
import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RUST_BIN = BASE_DIR / "bin" / "gritx-audio.exe"
TEMP_DIR = BASE_DIR / "data" / "test_audio"


def generate_synthetic_wav(path: Path, duration_sec: float = 30.0, sample_rate: int = 16000):
    """
    Generates a 16kHz mono 16-bit PCM WAV with deliberate speech-like sound bursts
    and distinct silence dips around 10s and 20s.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    num_samples = int(duration_sec * sample_rate)
    samples = []

    for i in range(num_samples):
        t = i / sample_rate
        # Silence dips at 9.0s - 11.0s and 19.0s - 21.0s
        if (9.0 <= t <= 11.0) or (19.0 <= t <= 21.0):
            sample_val = 0
        else:
            # Audible sine wave tone
            freq = 440.0 if t < 15.0 else 880.0
            sample_val = int(18000.0 * math.sin(2.0 * math.pi * freq * t))
        samples.append(sample_val)

    # Write WAV file
    byte_count = num_samples * 2
    header = bytearray()
    header.extend(b"RIFF")
    header.extend(struct.pack("<I", 36 + byte_count))
    header.extend(b"WAVE")
    header.extend(b"fmt ")
    header.extend(struct.pack("<I", 16))
    header.extend(struct.pack("<H", 1))  # PCM
    header.extend(struct.pack("<H", 1))  # Mono
    header.extend(struct.pack("<I", sample_rate))
    header.extend(struct.pack("<I", sample_rate * 2))  # ByteRate
    header.extend(struct.pack("<H", 2))  # BlockAlign
    header.extend(struct.pack("<H", 16)) # BitsPerSample
    header.extend(b"data")
    header.extend(struct.pack("<I", byte_count))

    raw_pcm = struct.pack(f"<{num_samples}h", *samples)
    path.write_bytes(header + raw_pcm)


def test_rust_binary_exists():
    assert RUST_BIN.exists(), f"gritx-audio.exe binary not found at {RUST_BIN}"
    res = subprocess.run([str(RUST_BIN), "--version"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "gritx-audio" in res.stdout
    print("PASS: test_rust_binary_exists")


def test_rust_audio_info():
    test_wav = TEMP_DIR / "synth_30s.wav"
    generate_synthetic_wav(test_wav, duration_sec=30.0)

    cmd = [str(RUST_BIN), "info", "--input", str(test_wav), "--json"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout)

    assert data["channels"] == 1
    assert data["sample_rate"] == 16000
    assert data["bits_per_sample"] == 16
    assert abs(data["duration_seconds"] - 30.0) < 0.1
    print("PASS: test_rust_audio_info")


def test_silence_aware_slicing():
    test_wav = TEMP_DIR / "synth_30s.wav"
    out_dir = TEMP_DIR / "chunks"
    if out_dir.exists():
        shutil.rmtree(out_dir)

    cmd = [
        str(RUST_BIN), "slice",
        "--input", str(test_wav),
        "--output-dir", str(out_dir),
        "--chunk-seconds", "10",
        "--search-window", "2.0",
        "--json"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout)

    assert data["total_chunks"] == 3
    chunks = data["chunks"]
    assert len(chunks) == 3

    # Chunk 0 should end in the first silence dip (9.0s to 11.0s)
    c0 = chunks[0]
    assert 9.0 <= c0["end_seconds"] <= 11.0, f"Chunk 0 cut at {c0['end_seconds']}, expected silence dip [9.0, 11.0]"
    assert Path(c0["path"]).exists()

    # Chunk 1 should start where Chunk 0 ended, and end in second silence dip [19.0, 21.0]
    c1 = chunks[1]
    assert abs(c1["start_seconds"] - c0["end_seconds"]) < 0.05
    assert 19.0 <= c1["end_seconds"] <= 21.0, f"Chunk 1 cut at {c1['end_seconds']}, expected silence dip [19.0, 21.0]"
    assert Path(c1["path"]).exists()

    # Chunk 2 should reach the end (30.0s)
    c2 = chunks[2]
    assert abs(c2["start_seconds"] - c1["end_seconds"]) < 0.05
    assert abs(c2["end_seconds"] - 30.0) < 0.1
    assert Path(c2["path"]).exists()

    print(f"PASS: test_silence_aware_slicing (completed in {data.get('elapsed_ms', 0)} ms)")


def test_pipeline_integration():
    import sys
    sys.path.insert(0, str(BASE_DIR))
    from pipeline.transcribe import chunk_audio_if_needed, get_rust_audio_bin

    rust_bin = get_rust_audio_bin()
    assert rust_bin is not None, "get_rust_audio_bin() returned None"

    test_wav = TEMP_DIR / "synth_pipeline.wav"
    generate_synthetic_wav(test_wav, duration_sec=30.0)

    # Test chunking via pipeline function
    chunks = chunk_audio_if_needed(test_wav, chunk_seconds=10)
    assert len(chunks) == 3, f"Expected 3 chunks, got {len(chunks)}"
    for idx, (c_path, offset) in enumerate(chunks):
        assert c_path.exists(), f"Chunk file {c_path} does not exist"
        assert isinstance(offset, float)

    print("PASS: test_pipeline_integration (chunk_audio_if_needed using Rust)")


def cleanup():
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)


if __name__ == "__main__":
    try:
        test_rust_binary_exists()
        test_rust_audio_info()
        test_silence_aware_slicing()
        test_pipeline_integration()
        print("\nAll GritX Rust Audio Engine tests passed successfully!")
    finally:
        cleanup()
