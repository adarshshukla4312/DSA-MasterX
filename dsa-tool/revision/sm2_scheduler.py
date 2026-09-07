import math
from datetime import datetime, timedelta
from pathlib import Path

from config import DB_PATH
from db.schema import get_connection, get_solved_problem_ids, get_all_problems

def calculate_sm2(quality: int, repetitions: int, ease_factor: float, interval: float) -> tuple[int, float, float]:
    """
    Core SM-2 algorithm.
    quality: 0-5 (0=complete blackout, 5=perfect response)
    Returns: (new_repetitions, new_ease_factor, new_interval_days)
    """
    if quality < 3:
        repetitions = 0
        interval = 1.0
    else:
        if repetitions == 0:
            interval = 1.0
        elif repetitions == 1:
            interval = 6.0
        else:
            interval = interval * ease_factor
        repetitions += 1
        
    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if ease_factor < 1.3:
        ease_factor = 1.3
        
    return repetitions, ease_factor, round(interval, 1)

def map_attempt_to_quality(solved: bool, difficulty_felt: int, used_hint: bool) -> int:
    """
    Maps attempt data to SM-2 quality (0-5).
    Assuming difficulty_felt is 1 (easy) to 5 (very hard)
    """
    if not solved:
        return 1 if used_hint else 0
        
    if used_hint:
        return 3 if difficulty_felt < 4 else 2
        
    if difficulty_felt <= 2:
        return 5
    elif difficulty_felt == 3:
        return 4
    else:
        return 3

def update_schedule(pattern: str, attempt_data: dict, db_path: str | Path) -> None:
    """Updates revision_schedule table based on new attempt."""
    conn = get_connection(db_path)
    
    # Get current schedule if it exists
    row = conn.execute("SELECT * FROM revision_schedule WHERE pattern = ?", (pattern,)).fetchone()
    
    if row:
        repetitions = row["repetitions"]
        ease_factor = row["ease_factor"]
        interval = row["interval"]
    else:
        repetitions = 0
        ease_factor = 2.5
        interval = 1.0
        
    quality = map_attempt_to_quality(
        bool(attempt_data.get("solved", False)),
        int(attempt_data.get("difficulty_felt", 3)),
        bool(attempt_data.get("used_hint", False))
    )
    
    new_rep, new_ef, new_int = calculate_sm2(quality, repetitions, ease_factor, interval)
    
    next_due = (datetime.now() + timedelta(days=new_int)).isoformat()
    now_iso = datetime.now().isoformat()
    
    conn.execute(
        """INSERT OR REPLACE INTO revision_schedule 
           (pattern, next_due_date, interval, ease_factor, repetitions, last_reviewed)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (pattern, next_due, new_int, new_ef, new_rep, now_iso)
    )
    
    conn.commit()
    conn.close()

def get_due_reviews(db_path: str | Path) -> list[dict]:
    """Gets patterns due today, each with one recommended unsolved problem."""
    conn = get_connection(db_path)
    now_iso = datetime.now().isoformat()
    
    rows = conn.execute(
        "SELECT * FROM revision_schedule WHERE next_due_date <= ? ORDER BY next_due_date ASC", 
        (now_iso,)
    ).fetchall()
    conn.close()
    
    due_patterns = [dict(r) for r in rows]
    
    # Recommend unsolved problems for due patterns
    solved_ids = get_solved_problem_ids(db_path)
    all_problems = get_all_problems(db_path)
    
    results = []
    for dp in due_patterns:
        pattern = dp["pattern"]
        # Find one unsolved problem matching this pattern
        recommended_prob = None
        for p in all_problems:
            if p["id"] not in solved_ids and pattern.lower() in [pat.lower() for pat in p.get("patterns", [])]:
                recommended_prob = p
                break
                
        dp["recommended_problem"] = recommended_prob
        results.append(dp)
        
    return results

def get_revision_stats(db_path: str | Path) -> dict:
    """Gets overall stats (total patterns, due today, mastered)."""
    conn = get_connection(db_path)
    now_iso = datetime.now().isoformat()
    
    total = conn.execute("SELECT COUNT(*) FROM revision_schedule").fetchone()[0]
    due = conn.execute("SELECT COUNT(*) FROM revision_schedule WHERE next_due_date <= ?", (now_iso,)).fetchone()[0]
    mastered = conn.execute("SELECT COUNT(*) FROM revision_schedule WHERE interval > 21").fetchone()[0]
    
    conn.close()
    
    return {
        "total_patterns": total,
        "due_today": due,
        "mastered": mastered
    }
