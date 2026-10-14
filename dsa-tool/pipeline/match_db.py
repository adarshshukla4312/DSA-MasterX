"""
GritX — State-of-the-Art Problem Matching & Candidate Retrieval
Combines:
1. Dense Semantic Vector Search (FastEmbed ONNX with BAAI/bge-small-en-v1.5)
2. Normalized Tag Overlap (Szymkiewicz–Simpson Overlap Coefficient)
3. Exact Title Resonance Detection
4. Robust Lexical Fallback
"""
import sqlite3
import re
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path

from config import DB_PATH
from db.schema import get_connection

logger = logging.getLogger(__name__)

TAG_ABBREVIATIONS = {
    "dfs": "depth first search",
    "bfs": "breadth first search",
    "dp": "dynamic programming",
    "bst": "binary search tree",
    "lca": "lowest common ancestor",
    "mst": "minimum spanning tree"
}


def normalize_tag(tag: str) -> str:
    """Normalizes a single pattern tag string."""
    if not tag:
        return ""
    t = tag.lower().replace("-", " ").strip()
    if t in TAG_ABBREVIATIONS:
        return TAG_ABBREVIATIONS[t]
    words = [w[:-1] if w.endswith("s") and len(w) > 3 and not w.endswith("ss") else w for w in t.split()]
    return " ".join(words)


def compute_tag_overlap(problem_patterns: List[str], candidate_patterns: List[str]) -> float:
    """
    Computes Szymkiewicz–Simpson overlap coefficient on normalized pattern tags.
    |A ∩ B| / min(|A|, |B|).
    Avoids penalizing comprehensive problems with many tags.
    """
    if not problem_patterns or not candidate_patterns:
        return 0.0

    set1 = set(normalize_tag(p) for p in problem_patterns if p)
    set2 = set(normalize_tag(p) for p in candidate_patterns if p)

    if not set1 or not set2:
        return 0.0

    intersection = len(set1.intersection(set2))
    min_size = min(len(set1), len(set2))

    if min_size == 0:
        return 0.0
    return intersection / min_size


def compute_title_resonance(cand_title: str, query_text: str) -> float:
    """Returns 1.0 if the candidate problem's title is explicitly mentioned in the query text."""
    if not cand_title or not query_text:
        return 0.0
    
    clean_title = re.sub(r"[^a-zA-Z0-9\s]", "", cand_title.lower()).strip()
    clean_query = re.sub(r"[^a-zA-Z0-9\s]", " ", query_text.lower())
    
    if len(clean_title) >= 4 and f" {clean_title} " in f" {clean_query} ":
        return 1.0
    return 0.0


def find_candidates(
    problem_desc: str,
    problem_patterns: List[str],
    all_problems: Optional[List[Dict]] = None,
    top_k: int = 25,
    db_path: str | Path = DB_PATH
) -> List[Dict]:
    """
    State-of-the-Art Hybrid Problem Retrieval:
    1. Vectorized dense semantic cosine similarity (< 0.1 ms)
    2. Overlap coefficient on pattern tags
    3. Exact title resonance bonus
    4. Graceful fallback to lexical overlap if vector search is unavailable
    """
    db_path = Path(db_path)

    # ─── 1. Attempt Dense Semantic Vector Retrieval ──────────────────────────
    try:
        from pipeline.embedding import semantic_search, build_query_document

        query_doc = build_query_document(problem_desc, problem_patterns)
        
        # Pull top 75 dense candidates to re-rank with hybrid signals
        dense_results = semantic_search(query_doc, db_path, top_k=max(top_k * 3, 75))

        if dense_results:
            hybrid_candidates = []
            for prob, dense_score in dense_results:
                cand_patterns = prob.get("patterns", [])
                if isinstance(cand_patterns, str):
                    try:
                        cand_patterns = json.loads(cand_patterns)
                    except Exception:
                        cand_patterns = []

                tag_score = compute_tag_overlap(problem_patterns, cand_patterns)
                title_score = compute_title_resonance(prob.get("title", ""), problem_desc)

                # Composite Hybrid Score
                # 85% Dense Semantic Vector + 10% Pattern Overlap + 5% Title Resonance
                composite_score = (
                    0.85 * max(dense_score, 0.0) +
                    0.10 * tag_score +
                    0.05 * title_score
                )

                hybrid_candidates.append({
                    "problem_id": prob["id"],
                    "title": prob["title"],
                    "platform": prob.get("platform", "LeetCode"),
                    "difficulty": prob.get("difficulty", "Medium"),
                    "score": round(composite_score, 4),
                    "dense_score": round(dense_score, 4),
                    "tag_score": round(tag_score, 4),
                    "patterns": cand_patterns,
                    "description": prob.get("description", ""),
                    "url": prob.get("url", "")
                })

            hybrid_candidates.sort(key=lambda x: x["score"], reverse=True)
            return hybrid_candidates[:top_k]

    except Exception as e:
        logger.warning(f"Dense vector retrieval bypassed ({e}), falling back to lexical scoring...")

    # ─── 2. Graceful Fallback: Tag Overlap + Word Jaccard ─────────────────────
    if all_problems is None:
        from db.schema import get_all_problems
        all_problems = get_all_problems(db_path)

    fallback_candidates = []
    query_words = set(re.findall(r"\b\w+\b", problem_desc.lower()))

    for prob in all_problems:
        cand_patterns = prob.get("patterns", [])
        if isinstance(cand_patterns, str):
            try:
                cand_patterns = json.loads(cand_patterns)
            except Exception:
                cand_patterns = []

        cand_desc = (prob.get("description", "") + " " + prob.get("title", "")).lower()
        cand_words = set(re.findall(r"\b\w+\b", cand_desc))

        tag_score = compute_tag_overlap(problem_patterns, cand_patterns)
        
        # Word overlap
        inter = len(query_words.intersection(cand_words))
        min_w = min(len(query_words), len(cand_words)) if (query_words and cand_words) else 1
        word_score = inter / min_w if min_w > 0 else 0.0

        title_score = compute_title_resonance(prob.get("title", ""), problem_desc)

        composite_score = 0.50 * word_score + 0.35 * tag_score + 0.15 * title_score

        fallback_candidates.append({
            "problem_id": prob["id"],
            "title": prob["title"],
            "platform": prob.get("platform", "LeetCode"),
            "difficulty": prob.get("difficulty", "Medium"),
            "score": round(composite_score, 4),
            "patterns": cand_patterns,
            "description": prob.get("description", ""),
            "url": prob.get("url", "")
        })

    fallback_candidates.sort(key=lambda x: x["score"], reverse=True)
    return fallback_candidates[:top_k]


def store_candidates(
    lecture_id: str,
    problem_desc: str,
    candidates: List[Dict],
    db_path: str | Path,
    confirmed: int = 1
) -> None:
    """Stores candidate matches in lecture_problem_matches table."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    for cand in candidates:
        reasoning = cand.get("reasoning") or f"Matched via hybrid semantic search (score: {cand.get('score', 1.0)})"
        try:
            cursor.execute(
                """INSERT OR REPLACE INTO lecture_problem_matches 
                   (lecture_id, problem_id, confirmed, match_reasoning, match_score)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    lecture_id,
                    cand["problem_id"],
                    confirmed,
                    reasoning,
                    cand.get("score", 1.0),
                ),
            )
        except sqlite3.Error as e:
            logger.error(f"Error storing candidate {cand.get('problem_id')}: {e}")

    conn.commit()
    conn.close()
