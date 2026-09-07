import sqlite3
import re
from typing import List, Dict
from pathlib import Path
from db.schema import get_connection

TAG_ABBREVIATIONS = {
    'dfs': 'depth first search',
    'bfs': 'breadth first search',
    'dp': 'dynamic programming',
    'bst': 'binary search tree',
    'lca': 'lowest common ancestor'
}

def normalize_tag(tag: str) -> str:
    t = tag.lower().replace('-', ' ').strip()
    if t in TAG_ABBREVIATIONS:
        return TAG_ABBREVIATIONS[t]
    words = [w[:-1] if w.endswith('s') and len(w) > 3 and not w.endswith('ss') else w for w in t.split()]
    return ' '.join(words)

def compute_tag_overlap(problem_patterns: List[str], candidate_patterns: List[str]) -> float:
    """Jaccard similarity on normalized pattern tags."""
    if not problem_patterns and not candidate_patterns:
        return 0.0
        
    set1 = set(normalize_tag(p) for p in problem_patterns if p)
    set2 = set(normalize_tag(p) for p in candidate_patterns if p)
    
    if not set1 and not set2:
        return 0.0
        
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    if union == 0:
        return 0.0
    return intersection / union

SYNONYM_GROUPS = [
    {'mirror', 'invert', 'flip'},
    {'traversal', 'traverse', 'walk'},
    {'levelorder', 'level-order', 'bfs', 'breadth'},
    {'preorder', 'pre-order'},
    {'inorder', 'in-order'},
    {'postorder', 'post-order'},
    {'depth', 'height'},
    {'kth', 'k-th'},
    {'subsequence', 'substring'},
    {'lca', 'lowest common ancestor'},
    {'bst', 'binary search tree'}
]

def expand_synonyms(words: set) -> set:
    expanded = set(words)
    for group in SYNONYM_GROUPS:
        if words.intersection(group):
            expanded.update(group)
    return expanded

def compute_text_similarity(desc1: str, desc2: str) -> float:
    """Keyword overlap score with DSA synonym expansion."""
    if not desc1 or not desc2:
        return 0.0
        
    # Extract alphanumeric words
    words1 = set(re.findall(r'\b\w+\b', desc1.lower()))
    words2 = set(re.findall(r'\b\w+\b', desc2.lower()))
    
    # Remove common stop words (simplified list)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'its'}
    words1 -= stop_words
    words2 -= stop_words
    
    if not words1 or not words2:
        return 0.0
        
    words1_exp = expand_synonyms(words1)
    words2_exp = expand_synonyms(words2)

    intersection = len(words1_exp.intersection(words2_exp))
    union = len(words1_exp.union(words2_exp))
    
    if union == 0:
        return 0.0
    return intersection / union

def find_candidates(problem_desc: str, problem_patterns: List[str], all_problems: List[Dict], top_k: int = 3) -> List[Dict]:
    """Combines tag + text similarity, returns ranked candidates."""
    candidates = []
    
    for prob in all_problems:
        cand_patterns = prob.get("patterns", [])
        cand_desc = prob.get("description", "") + " " + prob.get("title", "")
        
        tag_score = compute_tag_overlap(problem_patterns, cand_patterns)
        text_score = compute_text_similarity(problem_desc, cand_desc)
        
        # Combine scores (giving equal weight)
        total_score = (tag_score + text_score) / 2.0
        
        candidates.append({
            "problem_id": prob["id"],
            "title": prob["title"],
            "score": total_score,
            "patterns": cand_patterns,
            "description": prob.get("description", "")
        })
        
    # Sort by score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:top_k]

def store_candidates(lecture_id: str, problem_desc: str, candidates: List[Dict], db_path: str | Path, confirmed: int = 1) -> None:
    """Stores in lecture_problem_matches table automatically as confirmed=1."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    for cand in candidates:
        reasoning = cand.get("reasoning") or f"Matched based on description: {problem_desc[:100]}..."
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
                    cand.get("score", 1.0)
                )
            )
        except sqlite3.Error as e:
            pass
            
    conn.commit()
    conn.close()
