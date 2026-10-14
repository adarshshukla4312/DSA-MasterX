"""
GritX — Standalone CLI Pipeline Processor
Run lecture processing directly from terminal outside of browser/Streamlit.
"""
import sys
import argparse
import logging
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config import DB_PATH
from db.schema import get_all_lectures, get_lecture
from pipeline.runner import run_full_pipeline_sync

# Configure clean terminal logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def list_lectures():
    """Lists all lectures and their current processing status."""
    lectures = get_all_lectures(DB_PATH)
    print(f"\n{'='*70}")
    print(f"{'ID':<35} | {'STATUS':<12} | {'TITLE'}")
    print(f"{'='*70}")
    for l in lectures:
        status = l.get("status", "new").upper()
        print(f"{l['id']:<35} | {status:<12} | {l['title']}")
    print(f"{'='*70}\nTotal lectures in database: {len(lectures)}\n")


def process_single(lecture_id: str, skip_transcription: bool = False, course_context: str = ""):
    """Processes a single lecture by ID."""
    print(f"\n🚀 Starting terminal processing for lecture: {lecture_id}")
    try:
        res = run_full_pipeline_sync(
            lecture_id=lecture_id,
            skip_transcription=skip_transcription,
            course_context=course_context
        )
        print(f"\n🎉 SUCCESS! Processing completed for '{lecture_id}'. Status: {res.get('status')}")
    except Exception as e:
        print(f"\n❌ FAILED! Error processing '{lecture_id}': {e}")
        sys.exit(1)


def process_all_unprocessed(skip_transcription: bool = False):
    """Processes all lectures whose status is not 'completed'."""
    lectures = get_all_lectures(DB_PATH)
    unprocessed = [l for l in lectures if l.get("status") != "completed"]

    if not unprocessed:
        print("\n✅ All lectures are already completed!")
        return

    print(f"\nFound {len(unprocessed)} unprocessed lecture(s):")
    for l in unprocessed:
        print(f"  - [{l.get('status', 'new')}] {l['id']} ({l['title']})")

    for idx, l in enumerate(unprocessed, 1):
        print(f"\n{'='*70}")
        print(f"Processing ({idx}/{len(unprocessed)}): {l['id']} — {l['title']}")
        print(f"{'='*70}")
        try:
            run_full_pipeline_sync(
                lecture_id=l["id"],
                skip_transcription=skip_transcription
            )
        except Exception as e:
            print(f"❌ Error processing {l['id']}: {e}. Skipping to next...")

    print(f"\n🎉 Batch processing completed across {len(unprocessed)} lectures!")


def main():
    parser = argparse.ArgumentParser(description="GritX — CLI Pipeline Processor")
    parser.add_argument("--lecture", "-l", type=str, help="Lecture ID to process (e.g. '45-advanced-dsa-arrays-1')")
    parser.add_argument("--all", "-a", action="store_true", help="Process all unprocessed lectures in database")
    parser.add_argument("--list", action="store_true", help="List all lectures and their status")
    parser.add_argument("--skip-transcription", action="store_true", help="Skip Whisper transcription and use existing transcript file")
    parser.add_argument("--context", type=str, default="", help="Optional course context string")

    args = parser.parse_args()

    if args.list:
        list_lectures()
    elif args.lecture:
        process_single(args.lecture, skip_transcription=args.skip_transcription, course_context=args.context)
    elif args.all:
        process_all_unprocessed(skip_transcription=args.skip_transcription)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
