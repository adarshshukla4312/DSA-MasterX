"""
Unit tests for the resilient LLM engine: truncation detection, JSON repair,
stream buffer salvage, and extended timeouts.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from config import LLM_NON_STREAMING_TIMEOUT
from pipeline.resilient_llm import (
    clean_json_fences,
    is_json_incomplete,
    salvage_completed_elements,
    resilient_json_parse,
)

def test_non_streaming_timeout_is_7_minutes():
    """Verify non-streaming timeout is configured to 420 seconds (7 minutes)."""
    assert LLM_NON_STREAMING_TIMEOUT == 420.0, f"Expected 420.0, got {LLM_NON_STREAMING_TIMEOUT}"


def test_clean_json_fences():
    raw = "```json\n{\"topics\": [\"Arrays\"]}\n```"
    assert clean_json_fences(raw) == '{"topics": ["Arrays"]}'
    
    raw2 = "```\n{\"difficulty\": \"Advanced\"}\n```"
    assert clean_json_fences(raw2) == '{"difficulty": "Advanced"}'


def test_is_json_incomplete_valid():
    valid = '{"topics": ["Arrays"], "techniques": ["Two Pointers"]}'
    incomplete, reason = is_json_incomplete(valid)
    assert not incomplete
    assert "Complete valid JSON" in reason


def test_is_json_incomplete_unclosed_string():
    truncated = '{"topics": ["Arrays"], "description": "Given an array of integers, find the miss'
    incomplete, reason = is_json_incomplete(truncated)
    assert incomplete
    assert "Does not end with closing brace" in reason or "Odd number of unescaped quotes" in reason or "Unbalanced" in reason


def test_is_json_incomplete_unbalanced_braces():
    truncated = '{"topics": ["Arrays"], "problems": [{"name": "P1"}'
    incomplete, reason = is_json_incomplete(truncated)
    assert incomplete
    assert "Unbalanced" in reason


def test_resilient_json_parse_with_trailing_commas():
    # Standard json.loads fails on trailing comma
    bad_syntax = '{"topics": ["Arrays", "Hashing",], "difficulty": "Medium",}'
    parsed = resilient_json_parse(bad_syntax)
    assert parsed["topics"] == ["Arrays", "Hashing"]
    assert parsed["difficulty"] == "Medium"


def test_resilient_json_parse_with_unescaped_internal_quotes():
    # Unescaped quotes inside string
    bad_syntax = '{"steps": ["Use "solve" function to search matrix", "return answer"]}'
    parsed = resilient_json_parse(bad_syntax)
    assert len(parsed["steps"]) == 2
    assert "solve" in parsed["steps"][0]


def test_salvage_completed_elements_from_truncated_stream():
    # Simulate stream severed mid-generation at problem 3
    truncated_payload = '''
    {
      "topics": ["Arrays"],
      "problems_discussed": [
        {
          "name": "Missing Number",
          "core_trick": "Sum formula n*(n+1)/2",
          "time_complexity": "O(N)"
        },
        {
          "name": "Longest Consecutive Sequence",
          "core_trick": "HashSet predecessor check",
          "time_complexity": "O(N)"
        },
        {
          "name": "Search 2D Matrix",
          "core_trick": "Staircase search from top-right corner
    '''
    salvaged = salvage_completed_elements(truncated_payload, list_key="problems_discussed")
    assert len(salvaged) == 2
    assert salvaged[0]["name"] == "Missing Number"
    assert salvaged[1]["name"] == "Longest Consecutive Sequence"


def test_resilient_json_parse_auto_closes_truncated_stream():
    truncated = '{"topics": ["Arrays", "2D Arrays"], "techniques": ["Staircase Search"'
    parsed = resilient_json_parse(truncated)
    assert parsed["topics"] == ["Arrays", "2D Arrays"]
    assert "Staircase Search" in parsed["techniques"]


if __name__ == "__main__":
    tests = [
        test_non_streaming_timeout_is_7_minutes,
        test_clean_json_fences,
        test_is_json_incomplete_valid,
        test_is_json_incomplete_unclosed_string,
        test_is_json_incomplete_unbalanced_braces,
        test_resilient_json_parse_with_trailing_commas,
        test_resilient_json_parse_with_unescaped_internal_quotes,
        test_salvage_completed_elements_from_truncated_stream,
        test_resilient_json_parse_auto_closes_truncated_stream,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__} - {e}")
            raise
    print(f"\nAll {passed}/{len(tests)} tests passed successfully!")
