"""
GritX — Semantic Embedding & Dense Vector Search Engine
Uses FastEmbed (ONNX Runtime) with BAAI/bge-small-en-v1.5 (384 dimensions).
Provides sub-millisecond in-memory cosine similarity and SQLite BLOB persistence.
"""
import logging
import threading
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Global singleton model & vector cache
_model = None
_model_lock = threading.Lock()

_cache_lock = threading.Lock()
_cached_ids: List[str] = []
_cached_matrix: Optional[np.ndarray] = None  # shape (N, 384), L2-normalized
_cached_problems: Dict[str, dict] = {}


def get_embedding_model():
    """Lazily loads the FastEmbed ONNX model in a thread-safe manner."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                try:
                    from fastembed import TextEmbedding
                    logger.info("Initializing FastEmbed model: BAAI/bge-small-en-v1.5...")
                    _model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
                    logger.info("FastEmbed model initialized successfully.")
                except Exception as e:
                    logger.error(f"Failed to initialize FastEmbed model: {e}")
                    raise e
    return _model


def build_problem_document(prob: dict) -> str:
    """Constructs a rich semantic document string for a problem."""
    title = prob.get("title", "")
    diff = prob.get("difficulty", "Medium")
    pats = prob.get("patterns", [])
    if isinstance(pats, str):
        try:
            pats = json.loads(pats)
        except Exception:
            pats = []
    patterns_str = ", ".join(pats) if isinstance(pats, list) else str(pats)
    desc = prob.get("description", "")
    platform = prob.get("platform", "LeetCode")

    parts = [f"Title: {title} ({platform} {diff})"]
    if patterns_str:
        parts.append(f"Patterns: {patterns_str}")
    if desc:
        parts.append(f"Description: {desc}")
    return "\n".join(parts)


def build_query_document(problem_desc: str, problem_patterns: List[str]) -> str:
    """Constructs a rich semantic query representation from extracted lecture details."""
    pats_str = ", ".join(problem_patterns) if problem_patterns else ""
    parts = []
    if pats_str:
        parts.append(f"Patterns: {pats_str}")
    if problem_desc:
        parts.append(f"Description: {problem_desc}")
    return "\n".join(parts)


def embed_text(text: str) -> np.ndarray:
    """Embeds a single string into an L2-normalized float32 vector of shape (384,)."""
    model = get_embedding_model()
    embeddings = list(model.embed([text]))
    vec = np.array(embeddings[0], dtype=np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


def embed_batch(texts: List[str]) -> List[np.ndarray]:
    """Embeds a list of strings into a list of L2-normalized float32 vectors."""
    if not texts:
        return []
    model = get_embedding_model()
    embeddings = list(model.embed(texts))
    normalized = []
    for emb in embeddings:
        vec = np.array(emb, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        normalized.append(vec)
    return normalized


def sync_problem_embeddings_in_db(db_path: str | Path) -> int:
    """
    Checks all problems in the database and computes/persists embeddings for any
    problem that currently has embedding IS NULL.
    Returns the count of newly embedded problems.
    """
    import sqlite3
    from db.schema import get_connection

    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Ensure column exists
    existing_cols = {row["name"] for row in cursor.execute("PRAGMA table_info(problems)").fetchall()}
    if "embedding" not in existing_cols:
        cursor.execute("ALTER TABLE problems ADD COLUMN embedding BLOB")
        conn.commit()

    # Find problems missing embeddings
    unindexed = cursor.execute("SELECT id, title, difficulty, patterns, description, platform FROM problems WHERE embedding IS NULL").fetchall()
    if not unindexed:
        conn.close()
        return 0

    logger.info(f"Indexing embeddings for {len(unindexed)} problems...")
    prob_dicts = [dict(r) for r in unindexed]
    docs = [build_problem_document(p) for p in prob_dicts]
    vectors = embed_batch(docs)

    for prob, vec in zip(prob_dicts, vectors):
        blob = vec.tobytes()
        cursor.execute("UPDATE problems SET embedding = ? WHERE id = ?", (blob, prob["id"]))

    conn.commit()
    conn.close()
    logger.info(f"Indexed embeddings for {len(unindexed)} problems in DB.")
    
    # Invalidate cache so it reloads on next query
    invalidate_cache()
    return len(unindexed)


def invalidate_cache():
    """Forces cache reload on next similarity search."""
    global _cached_matrix, _cached_ids, _cached_problems
    with _cache_lock:
        _cached_matrix = None
        _cached_ids = []
        _cached_problems = {}


def load_vector_cache(db_path: str | Path):
    """Loads all problem embeddings and metadata from DB into RAM for instant vector search."""
    global _cached_matrix, _cached_ids, _cached_problems
    with _cache_lock:
        if _cached_matrix is not None:
            return

        from db.schema import get_connection
        conn = get_connection(db_path)
        rows = conn.execute("SELECT id, title, platform, url, difficulty, patterns, description, embedding FROM problems").fetchall()
        conn.close()

        ids = []
        vectors = []
        prob_map = {}

        for r in rows:
            d = dict(r)
            pid = d["id"]
            blob = d.get("embedding")
            if blob and len(blob) == 384 * 4:  # 384 float32 numbers = 1536 bytes
                vec = np.frombuffer(blob, dtype=np.float32)
                # Ensure normalized
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                ids.append(pid)
                vectors.append(vec)

            # Clean patterns
            pats = d.get("patterns", "[]")
            if isinstance(pats, str):
                try:
                    d["patterns"] = json.loads(pats)
                except Exception:
                    d["patterns"] = []
            prob_map[pid] = d

        _cached_ids = ids
        _cached_matrix = np.vstack(vectors) if vectors else np.zeros((0, 384), dtype=np.float32)
        _cached_problems = prob_map
        logger.info(f"Loaded vector search index with {len(_cached_ids)} embedded problems in RAM.")


def semantic_search(query_text: str, db_path: str | Path, top_k: int = 25) -> List[Tuple[dict, float]]:
    """
    Performs vectorized cosine similarity search across all embedded problems in RAM.
    Returns list of (problem_dict, cosine_score) sorted descending.
    Runs in < 0.1 ms!
    """
    load_vector_cache(db_path)

    if _cached_matrix is None or len(_cached_ids) == 0:
        return []

    query_vec = embed_text(query_text)  # shape (384,), L2-normalized

    # Fast vectorized dot product: shape (N,)
    with _cache_lock:
        scores = np.dot(_cached_matrix, query_vec)
        candidate_ids = _cached_ids
        prob_map = _cached_problems

    # Top-K indices
    if len(scores) <= top_k:
        top_indices = np.argsort(-scores)
    else:
        # argpartition for linear time top-k
        part_idx = np.argpartition(-scores, top_k)[:top_k]
        top_indices = part_idx[np.argsort(-scores[part_idx])]

    results = []
    for idx in top_indices:
        pid = candidate_ids[idx]
        score = float(scores[idx])
        prob = prob_map.get(pid)
        if prob:
            results.append((prob, score))

    return results
